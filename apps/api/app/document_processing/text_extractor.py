from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def extract_text_from_document(file_name: str, content: bytes) -> tuple[str | None, str]:
    extension = Path(file_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return None, "Error de extraccion"

    if extension == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
        except Exception:
            return None, "Error de extraccion"

        if len(text) < 120:
            return text or None, "Requiere OCR"
        return text, "Texto extraido"

    if extension == ".docx":
        try:
            document = Document(BytesIO(content))
            paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
            text = "\n".join(paragraphs).strip()
        except Exception:
            return None, "Error de extraccion"

        if len(text) < 120:
            return text or None, "Requiere OCR"
        return text, "Texto extraido"

    # .doc legacy format is not parsed in this MVP.
    return None, "Error de extraccion"
