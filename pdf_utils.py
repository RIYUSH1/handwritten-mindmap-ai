import logging
import io
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PDFUtils")

def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """
    Safely retrieves the total number of pages in a PDF using PyMuPDF.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"Failed to count PDF pages with PyMuPDF: {e}")
        # Secondary check using pdf2image or a lightweight fallback if fitz fails
        try:
            from pdf2image import pdfinfo_from_bytes
            info = pdfinfo_from_bytes(pdf_bytes)
            return int(info.get("Pages", 1))
        except Exception as e2:
            logger.error(f"Secondary page count check also failed: {e2}")
            return 1


def convert_pdf_to_images(
    pdf_bytes: bytes,
    start_page: int = 1,
    end_page: int = None,
    dpi: int = 300
) -> list:
    """
    Dual-engine memory-efficient PDF page converter.
    Yields (page_number, PIL.Image) one by one to avoid memory bloat.
    
    Primary Engine: PyMuPDF (fitz) - Zero-setup, pure-pip compile, ultra-fast.
    Secondary Engine: pdf2image - Standard Poppler fallback.
    """
    total_pages = get_pdf_page_count(pdf_bytes)
    
    # Resolve page bounds (1-indexed bounds)
    start_page = max(1, start_page)
    if end_page is None or end_page > total_pages:
        end_page = total_pages
    
    logger.info(f"Converting PDF pages {start_page} to {end_page} of {total_pages} total pages (DPI: {dpi})...")

    # ----------------------------------------------------
    # PRIMARY ENGINE: PYMUPDF (fitz)
    # ----------------------------------------------------
    try:
        import fitz
        logger.info("Attempting PDF conversion using Primary Engine: PyMuPDF...")
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Scale factor for converting 72 DPI PDF standard to target DPI (e.g., 300 DPI)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        for page_idx in range(start_page - 1, end_page):
            page_num = page_idx + 1
            logger.info(f"Rendering page {page_num} using PyMuPDF...")
            
            page = doc.load_page(page_idx)
            # Render page to high-res pixmap
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert PyMuPDF samples to PIL Image
            # samples format matches standard RGB byte streams
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            yield page_num, img
            
        doc.close()
        logger.info("PyMuPDF processing completed successfully.")
        return

    except ImportError:
        logger.warning("PyMuPDF (fitz) is not installed. Falling back to pdf2image.")
    except Exception as fitz_err:
        logger.error(f"Primary PyMuPDF engine failed: {fitz_err}. Falling back to pdf2image...")

    # ----------------------------------------------------
    # SECONDARY ENGINE: PDF2IMAGE (Poppler Fallback)
    # ----------------------------------------------------
    try:
        from pdf2image import convert_from_bytes
        logger.info("Attempting PDF conversion using Secondary Engine: pdf2image...")
        
        # Convert pages within the requested bounds
        images = convert_from_bytes(
            pdf_bytes,
            dpi=dpi,
            first_page=start_page,
            last_page=end_page
        )
        
        for idx, img in enumerate(images):
            page_num = start_page + idx
            logger.info(f"Yielding page {page_num} converted via pdf2image...")
            yield page_num, img
            
        return

    except ModuleNotFoundError:
        raise RuntimeError(
            "❌ PDF Engine Error: Neither PyMuPDF nor pdf2image is available. "
            "Please check requirements.txt and verify packages."
        )
    except Exception as p_err:
        err_msg = str(p_err)
        if "poppler" in err_msg.lower() or "pdfinfo" in err_msg.lower():
            raise RuntimeError(
                "❌ Poppler Missing: pdf2image requires Poppler binary utilities to be installed on your system. "
                "To fix this, download Poppler for Windows and extract it, or use PyMuPDF by installing 'pymupdf'."
            )
        else:
            raise RuntimeError(f"❌ Failed to parse PDF file. Details: {err_msg}")
