"""
Extract raw text from PDFs (via PyMuPDF / fitz) or plain-text files.
"""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extract_text(filepath: str) -> str:
    """Route to the right extractor based on file extension."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    else:
        return path.read_text(encoding="utf-8", errors="ignore")


def _extract_pdf(path: Path) -> str:
    """Open a PDF with PyMuPDF, concatenate every page's text."""
    import fitz

    doc = fitz.open(str(path))
    pages = len(doc)
    text = []
    for page in doc:
        text.append(page.get_text())
    doc.close()

    result = "\n\n".join(text).strip()
    logger.info(f"Extracted {len(result)} chars from {path.name} ({pages} pages)")
    return result or "[No extractable text found]"