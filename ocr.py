import os
import logging
import numpy as np
import pytesseract
import easyocr
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OCR")

# Global Cache for EasyOCR Readers to avoid loading models repeatedly (which is very slow)
_easyocr_readers = {}

# Tesseract Executable Auto-Discovery on Windows
def auto_discover_tesseract():
    """
    Attempts to find Tesseract-OCR executable in common Windows installation paths
    if it is not already accessible globally in the system PATH.
    """
    # 1. Check if Tesseract is already in PATH
    import shutil
    if shutil.which("tesseract"):
        logger.info("Tesseract found in system PATH. Auto-discovery completed.")
        return

    # 2. Check standard Windows installation paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\ASUS\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",  # Specific to current user path if locally installed
    ]
    
    # Generic user path checking
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        possible_paths.append(os.path.join(user_profile, "AppData", "Local", "Programs", "Tesseract-OCR", "tesseract.exe"))

    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Tesseract binary auto-discovered and set to: {path}")
            return
            
    logger.warning("Tesseract binary could not be found in common paths. Make sure it is installed and added to your system PATH.")

# Run auto-discovery at import time
auto_discover_tesseract()


def get_easyocr_reader(lang: str = "en") -> easyocr.Reader:
    """
    Returns a cached EasyOCR Reader instance for the requested language.
    Prevents reloading models (saves 2-4 seconds per call).
    """
    global _easyocr_readers
    if lang not in _easyocr_readers:
        logger.info(f"Loading EasyOCR model for language '{lang}'...")
        # Check if CUDA/GPU is available for acceleration
        import torch
        gpu_available = torch.cuda.is_available()
        logger.info(f"CUDA/GPU available for EasyOCR: {gpu_available}")
        
        _easyocr_readers[lang] = easyocr.Reader([lang], gpu=gpu_available)
        logger.info(f"EasyOCR model '{lang}' loaded successfully.")
    return _easyocr_readers[lang]


def run_pytesseract_ocr(image_np: np.ndarray) -> str:
    """
    Extracts text from a preprocessed image array using Tesseract OCR.
    """
    try:
        # Tesseract configuration for optimal performance:
        # --oem 3: Default OCR Engine Mode (LSTM neural network)
        # --psm 3: Fully automatic page segmentation mode, but no OSD
        config = "--oem 3 --psm 3"
        text = pytesseract.image_to_string(image_np, config=config)
        return text.strip()
    except Exception as e:
        logger.error(f"PyTesseract execution failed: {e}")
        raise RuntimeError("Tesseract engine failed or not configured properly.")


def run_easyocr_ocr(image_np: np.ndarray) -> str:
    """
    Extracts text from a preprocessed image array using EasyOCR.
    Filters noise and aggregates sentences keeping structure.
    """
    try:
        reader = get_easyocr_reader("en")
        results = reader.readtext(image_np)
        
        lines = []
        for box, text, conf in results:
            # Filter extremely low-confidence reading errors
            if conf >= 0.35 and len(text.strip()) > 1:
                lines.append(text.strip())
                
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"EasyOCR execution failed: {e}")
        raise RuntimeError(f"EasyOCR engine failed: {str(e)}")


def extract_text(
    image_np: np.ndarray,
    engine: str = "EasyOCR"
) -> tuple:
    """
    Orchestrates text extraction from a preprocessed image numpy array.
    Supports automatic engine fallback with graceful recovery:
    - If Tesseract fails/missing -> Falls back to EasyOCR
    - If EasyOCR fails -> Falls back to Tesseract (if possible)
    
    Returns:
        tuple: (extracted_text_string, finalized_engine_name, fallback_warning_or_none)
    """
    engine = engine.strip().lower()
    warning_msg = None

    # Case 1: Tesseract selected
    if "tesseract" in engine:
        try:
            logger.info("Executing PyTesseract OCR...")
            text = run_pytesseract_ocr(image_np)
            return text, "PyTesseract", None
        except Exception as e:
            warning_msg = (
                "⚠️ PyTesseract was unavailable or threw an error. "
                "Automatically fell back to EasyOCR to continue processing."
            )
            logger.warning(warning_msg)
            try:
                text = run_easyocr_ocr(image_np)
                return text, "EasyOCR (Fallback)", warning_msg
            except Exception as e_fallback:
                raise RuntimeError(
                    f"❌ Both OCR engines failed. Primary error: {str(e)}. "
                    f"Fallback error: {str(e_fallback)}"
                )

    # Case 2: EasyOCR selected (Default)
    else:
        try:
            logger.info("Executing EasyOCR...")
            text = run_easyocr_ocr(image_np)
            return text, "EasyOCR", None
        except Exception as e:
            warning_msg = (
                "⚠️ EasyOCR threw an error. "
                "Automatically fell back to PyTesseract to continue processing."
            )
            logger.warning(warning_msg)
            try:
                text = run_pytesseract_ocr(image_np)
                return text, "PyTesseract (Fallback)", warning_msg
            except Exception as e_fallback:
                raise RuntimeError(
                    f"❌ Both OCR engines failed. Primary error: {str(e)}. "
                    f"Fallback error: {str(e_fallback)}"
                )
