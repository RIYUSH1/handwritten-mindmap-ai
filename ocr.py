import easyocr
import numpy as np
from PIL import Image

# Initialize OCR reader (English)
reader = easyocr.Reader(['en'], gpu=False)

def extract_text(image_path):
    # Open image
    img = Image.open(image_path)

    # Convert PIL image to numpy array
    img_np = np.array(img)

    # Perform OCR
    results = reader.readtext(img_np)

    # Combine detected text
    text = " ".join([res[1] for res in results])

    return text
