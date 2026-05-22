from pypdf import PdfReader

from config import MAX_CONTEXT_CHARS
from core.utils import safe_truncate


class PDFReadError(Exception):
    pass


def read_pdf(path: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    try:
        reader = PdfReader(path)
    except Exception as e:
        raise PDFReadError(f"Gagal membuka PDF: {e}")

    parts = []

    try:
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                parts.append(f"--- Page {i} ---\n{text.strip()}")

            if sum(len(x) for x in parts) >= max_chars:
                break

    except Exception as e:
        raise PDFReadError(f"Gagal membaca isi PDF: {e}")

    result = "\n\n".join(parts).strip()

    if not result:
        raise PDFReadError(
            "PDF tidak punya text layer yang terbaca. Kemungkinan perlu OCR/Vision."
        )

    return safe_truncate(result, max_chars)
