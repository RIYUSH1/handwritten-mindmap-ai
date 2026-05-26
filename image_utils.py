import numpy as np
import logging
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ImageUtils")

# Safe OpenCV Import
try:
    import cv2
    HAS_CV2 = True
    logger.info("OpenCV (cv2) imported successfully.")
except ImportError as e:
    HAS_CV2 = False
    logger.warning(f"OpenCV (cv2) import failed: {e}. Falling back to PIL-only image preprocessing.")

def load_image_safely(image_input) -> Image.Image:
    """
    Safely loads an image from a path or file-like object,
    corrects EXIF orientation, and flattens transparency (RGBA -> RGB).
    """
    try:
        if isinstance(image_input, (str, bytes)):
            # Load from file path or raw bytes
            if isinstance(image_input, bytes):
                import io
                image = Image.open(io.BytesIO(image_input))
            else:
                image = Image.open(image_input)
        else:
            # Assume it's a file-like object from Streamlit uploader
            image = Image.open(image_input)

        # 1. Correct Orientation using EXIF data
        try:
            image = ImageOps.exif_transpose(image)
        except Exception as exif_err:
            logger.warning(f"Failed to correct EXIF orientation: {exif_err}")

        # 2. Handle transparency (RGBA/LA) or Palette modes
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            logger.info(f"Flattening transparency from mode: {image.mode}")
            image = image.convert("RGBA")
            # Create a solid white background canvas
            background = Image.new("RGBA", image.size, (255, 255, 255, 255))
            # Paste image onto white background using alpha channel as mask
            flat_image = Image.alpha_composite(background, image)
            return flat_image.convert("RGB")
        else:
            return image.convert("RGB")

    except Exception as e:
        logger.error(f"Error loading image safely: {str(e)}")
        raise ValueError(f"❌ Corrupted or unsupported image file. Details: {str(e)}")


def resize_image_optimally(image: Image.Image, target_width: int = 1800) -> Image.Image:
    """
    Resizes image maintaining aspect ratio to prevent memory overflow (for extremely large images)
    or to upscale tiny images for better OCR character recognition.
    """
    try:
        width, height = image.size
        # If image is excessively large, scale down
        if width > 2500 or height > 2500:
            scale = target_width / float(width)
            new_height = int(float(height) * float(scale))
            logger.info(f"Resizing down huge image from ({width}x{height}) to ({target_width}x{new_height})")
            return image.resize((target_width, new_height), Image.Resampling.LANCZOS)
        
        # If image is too small for OCR, scale up
        elif width < 800:
            scale = 1200 / float(width)
            new_height = int(float(height) * float(scale))
            logger.info(f"Resizing up small image from ({width}x{height}) to (1200x{new_height}) for OCR enhancement")
            return image.resize((1200, new_height), Image.Resampling.LANCZOS)
            
        return image
    except Exception as e:
        logger.warning(f"Optimized resizing failed, using original: {e}")
        return image


def _preprocess_via_pil(
    image: Image.Image,
    grayscale: bool = True,
    sharpen: bool = True,
    denoise: bool = True,
    threshold: bool = True
) -> tuple:
    """
    Highly optimized image preprocessing fallback using pure PIL/Pillow.
    Matches standard OpenCV actions to provide stable, clean OCR text feed.
    """
    logger.info("Executing PIL/Pillow fallback preprocessing pipeline...")
    try:
        processed = image.copy()

        # 1. Grayscale conversion
        if grayscale:
            processed = processed.convert("L")
            logger.info("PIL: Grayscale conversion applied.")

        # 2. Denoising / Smoothing
        if denoise:
            # We use a Median Filter to preserve edges while removing salt-and-pepper noise
            processed = processed.filter(ImageFilter.MedianFilter(size=3))
            logger.info("PIL: Median filter denoising applied.")

        # 3. High-Pass Sharpening
        if sharpen:
            # First, boost contrast slightly to highlight stroke edges
            contrast_enhancer = ImageEnhance.Contrast(processed)
            processed = contrast_enhancer.enhance(1.4)
            # Then apply sharpening filter
            processed = processed.filter(ImageFilter.SHARPEN)
            sharp_enhancer = ImageEnhance.Sharpness(processed)
            processed = sharp_enhancer.enhance(1.5)
            logger.info("PIL: Edge and stroke sharpening applied.")

        # 4. Adaptive Thresholding equivalent (Numpy local mean thresholding or point threshold)
        if threshold:
            if processed.mode != "L":
                processed = processed.convert("L")
            
            # Using simple adaptive thresholding on NumPy array for accuracy
            arr = np.array(processed)
            
            # Block-based local thresholding in Pure NumPy:
            # We calculate a simple local threshold using a uniform filter equivalent (numpy box blur)
            from scipy.ndimage import uniform_filter
            # Safe scipy import
            try:
                # Apply 15x15 uniform filter to compute local means
                local_mean = uniform_filter(arr.astype(float), size=15, mode='reflect')
                # Subtract constant C (like OpenCV adaptiveThreshold)
                bin_arr = np.where(arr < (local_mean - 4), 0, 255).astype(np.uint8)
                processed_np = bin_arr
                pil_out = Image.fromarray(processed_np)
                logger.info("PIL + NumPy: Advanced local adaptive thresholding applied.")
            except Exception as numpy_thresh_err:
                logger.warning(f"Local numpy thresholding failed: {numpy_thresh_err}. Using global Otsu-style point threshold.")
                # Fallback to high-contrast binarization point filter
                thresh_val = 127
                # Quick point thresholding
                pil_out = processed.point(lambda p: 255 if p > thresh_val else 0, "1")
                processed_np = np.array(pil_out.convert("L"))
        else:
            processed_np = np.array(processed)
            pil_out = processed

        return processed_np, pil_out

    except Exception as e:
        logger.error(f"PIL fallback preprocessing failed: {e}")
        # Final emergency return of raw image
        raw_gray = image.convert("L")
        return np.array(raw_gray), image


def preprocess_for_ocr(
    image: Image.Image,
    grayscale: bool = True,
    sharpen: bool = True,
    denoise: bool = True,
    threshold: bool = True
) -> tuple:
    """
    Applies an elite OpenCV-based preprocessing pipeline to optimize handwritten text extraction:
    - Grayscale conversion
    - Edge-preserving bilateral denoising
    - High-pass stroke sharpening
    - Adaptive Gaussian C thresholding to handle lighting gradients/shadows
    
    If cv2 is unavailable or raises an error, gracefully degrades to high-fidelity PIL-based pipeline.
    
    Returns:
        tuple: (preprocessed_numpy_array, preprocessed_PIL_image)
    """
    if not HAS_CV2:
        return _preprocess_via_pil(image, grayscale, sharpen, denoise, threshold)

    try:
        # Convert PIL Image to OpenCV BGR numpy array
        img_np = np.array(image)
        # Convert RGB to BGR for OpenCV standard handling
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        processed = img_cv.copy()

        # 1. Grayscale Conversion
        if grayscale:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            logger.info("Grayscale conversion applied.")

        # 2. Denoising (Edge-preserving Bilateral Filter)
        if denoise:
            if len(processed.shape) == 3:
                processed = cv2.bilateralFilter(processed, 9, 75, 75)
            else:
                # Bilateral Filter on grayscale
                processed = cv2.bilateralFilter(processed, 9, 50, 50)
            logger.info("Bilateral noise filtering applied.")

        # 3. High-Pass Sharpening (enhances thin handwriting pencil/pen strokes)
        if sharpen:
            # Sharpening kernel
            kernel = np.array([
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0]
            ])
            processed = cv2.filter2D(processed, -1, kernel)
            logger.info("Stroke sharpening filter applied.")

        # 4. Adaptive Thresholding (handles shadows, creases, and low-contrast handwriting)
        if threshold:
            if len(processed.shape) == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
            # Apply Adaptive Gaussian Thresholding
            processed = cv2.adaptiveThreshold(
                processed,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                15,  # Block size
                4    # Constant C subtracted from mean
            )
            logger.info("Adaptive Gaussian thresholding applied.")

        # Convert back to PIL Image for Streamlit preview rendering
        if len(processed.shape) == 2:
            # Grayscale / Binary
            pil_out = Image.fromarray(processed)
        else:
            # Color
            pil_out = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))

        return processed, pil_out

    except Exception as e:
        logger.error(f"OpenCV preprocessing failed: {str(e)}. Attempting PIL fallback...")
        try:
            return _preprocess_via_pil(image, grayscale, sharpen, denoise, threshold)
        except Exception as e_fallback:
            logger.critical(f"Both OpenCV and PIL fallback preprocessing pipelines failed: {e_fallback}")
            # Absolute safety fallback: return grayscale numpy array and raw PIL image
            fallback_gray = image.convert("L")
            return np.array(fallback_gray), image
