from pathlib import Path

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_from_file(file_path):
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            text_parts = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(part for part in text_parts if part).strip() or None

    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        with Image.open(path) as image:
            text = pytesseract.image_to_string(image)
        return text.strip() or None

    return None
