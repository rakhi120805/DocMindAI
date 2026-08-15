"""
Preprocessing — turns a file on disk into a list of clean page images,
ready for OCR.

WHY THIS IS SEPARATE FROM THE OCR ENGINE ITSELF (paddleocr_engine.py):
Rendering a PDF page to an image and enhancing that image are generic
image-processing concerns that have nothing to do with which OCR
engine reads the text afterward. Keeping them apart means you could
swap PaddleOCR for Tesseract or a cloud OCR API without touching this
file at all.
"""

from pathlib import Path
from typing import List
from PIL import Image, ImageOps, ImageFilter


SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def load_pages_as_images(file_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Accepts either a PDF or a plain image file and returns a list of
    PIL Images — one per page (a plain image file is just "one page").

    WHY 300 DPI: OCR accuracy improves noticeably with higher resolution
    than a typical screen (72-150 DPI), because small/blurry characters
    are the #1 cause of misreads. 300 DPI is the standard sweet spot
    used by most document-scanning pipelines — high enough for accuracy,
    not so high that render time/memory become a problem.
    """
    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        return _render_pdf_pages(path, dpi=dpi)
    elif path.suffix.lower() in SUPPORTED_IMAGE_EXTS:
        return [Image.open(path).convert("RGB")]
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def _render_pdf_pages(path: Path, dpi: int) -> List[Image.Image]:
    import fitz  # PyMuPDF - imported here so the rest of the app can
                 # still be imported/tested without it installed

    doc = fitz.open(path)
    zoom = dpi / 72  # PyMuPDF's default render resolution is 72 DPI
    matrix = fitz.Matrix(zoom, zoom)

    images = []
    for page in doc:
        pixmap = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        images.append(img)
    return images


def enhance_image(image: Image.Image) -> Image.Image:
    """
    Cheap, fast enhancements that measurably help OCR accuracy on
    scanned/photographed documents:
      1. Grayscale - color information doesn't help OCR and slows it down
      2. Autocontrast - stretches faint scans to use the full brightness
         range, so light gray text on white becomes properly readable
      3. Slight sharpen - counteracts the blur from photographing a
         document at an angle or with a shaky hand

    We deliberately DON'T do heavy deskewing/binarization here - those
    need more careful tuning per document type, and it's easy to make
    OCR worse by over-processing. Start simple, measure OCR accuracy
    (see evaluation/metrics.py), then add more only if it helps.
    """
    gray = ImageOps.grayscale(image)
    contrasted = ImageOps.autocontrast(gray, cutoff=1)
    sharpened = contrasted.filter(ImageFilter.SHARPEN)
    return sharpened
