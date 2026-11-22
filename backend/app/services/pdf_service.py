"""Policy PDF text extraction using PyMuPDF."""
from __future__ import annotations

import fitz  # PyMuPDF


class PdfExtractionError(Exception):
    """Raised when an uploaded file cannot be read as a PDF."""


def extract_text_from_pdf(data: bytes) -> str:
    """Return the concatenated text of every page in the PDF.

    Raises PdfExtractionError for invalid or unreadable files so the caller can
    return a proper 4xx response instead of a fake success.
    """
    if not data:
        raise PdfExtractionError("The uploaded file is empty.")
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # noqa: BLE001 - surfaced to the API layer
        raise PdfExtractionError(f"Not a valid PDF: {exc}") from exc

    try:
        if document.is_encrypted and not document.authenticate(""):
            raise PdfExtractionError("The PDF is password protected.")
        pages = [page.get_text("text") for page in document]
    finally:
        document.close()

    text = "\n".join(pages).strip()
    if len(text) < 20:
        raise PdfExtractionError(
            "No selectable text found. The PDF may be a scanned image."
        )
    return text
