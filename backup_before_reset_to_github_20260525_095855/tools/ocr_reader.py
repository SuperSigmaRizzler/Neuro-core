import base64
import mimetypes
from pathlib import Path
from typing import Optional

from config import IMAGE_EXTS, MAX_PROVIDER_ATTEMPTS, MISTRAL_API_KEYS, PDF_EXTS
from providers.key_utils import masked_secret, pick_attempt_keys


class OCRError(Exception):
    pass


def _is_url(value: str) -> bool:
    return str(value or "").startswith("http://") or str(value or "").startswith("https://")


def _path_to_data_url(path: str) -> str:
    p = Path(path)
    mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    data = base64.b64encode(p.read_bytes()).decode("utf-8")

    return f"data:{mime};base64,{data}"


def _ocr_with_paddle(path: str) -> str:
    if _is_url(path):
        raise OCRError("PaddleOCR lokal butuh file lokal, bukan URL.")

    p = Path(path)

    if not p.exists():
        raise OCRError("File tidak ditemukan untuk OCR lokal.")

    if p.suffix.lower() not in IMAGE_EXTS:
        raise OCRError("PaddleOCR lokal saat ini hanya untuk image file.")

    try:
        from paddleocr import PaddleOCR
    except Exception as e:
        raise OCRError(f"PaddleOCR belum terinstall / gagal import: {e}")

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en")
        output = ocr.ocr(str(p), cls=True)

        lines = []

        for page in output or []:
            for row in page or []:
                try:
                    text = row[1][0]

                    if text:
                        lines.append(text)

                except Exception:
                    continue

        result = "\n".join(lines).strip()

        if not result:
            raise OCRError("PaddleOCR tidak menemukan teks.")

        return result

    except Exception as e:
        raise OCRError(f"PaddleOCR gagal: {e}")


def _extract_mistral_markdown(result) -> str:
    pages = getattr(result, "pages", None)

    if pages is None and isinstance(result, dict):
        pages = result.get("pages")

    chunks = []

    for page in pages or []:
        if isinstance(page, dict):
            markdown = page.get("markdown") or ""
        else:
            markdown = getattr(page, "markdown", "") or ""

        if markdown.strip():
            chunks.append(markdown.strip())

    return "\n\n".join(chunks).strip()


def _ocr_with_mistral(source: str) -> str:
    keys = pick_attempt_keys(MISTRAL_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise OCRError("MISTRAL_API_KEYS / MISTRAL_API_KEY belum diisi untuk fallback OCR.")

    try:
        from mistralai import Mistral
    except Exception as e:
        raise OCRError(f"Package mistralai belum terinstall / gagal import: {e}")

    is_url = _is_url(source)
    suffix = "" if is_url else Path(source).suffix.lower()

    if is_url:
        lower = source.lower().split("?")[0]

        if any(lower.endswith(ext) for ext in IMAGE_EXTS):
            document = {
                "type": "image_url",
                "image_url": source
            }
        else:
            document = {
                "type": "document_url",
                "document_url": source
            }

    else:
        if suffix in IMAGE_EXTS:
            document = {
                "type": "image_url",
                "image_url": _path_to_data_url(source)
            }
        elif suffix in PDF_EXTS:
            document = {
                "type": "document_url",
                "document_url": _path_to_data_url(source)
            }
        else:
            raise OCRError("Mistral OCR fallback hanya untuk image/PDF.")

    last_error = None

    for key in keys:
        try:
            client = Mistral(api_key=key)
            result = client.ocr.process(
                model="mistral-ocr-latest",
                document=document,
                include_image_base64=False
            )

            text = _extract_mistral_markdown(result)

            if text:
                return text

            last_error = "Mistral OCR response kosong."

        except Exception as e:
            last_error = f"Mistral OCR gagal with key {masked_secret(key)}: {e}"
            continue

    raise OCRError(last_error or "Semua Mistral OCR key gagal.")


def ocr_file(path_or_url: str, allow_mistral_fallback: bool = True) -> str:
    paddle_error: Optional[str] = None

    try:
        return _ocr_with_paddle(path_or_url)

    except Exception as e:
        paddle_error = str(e)

    if allow_mistral_fallback:
        try:
            return _ocr_with_mistral(path_or_url)

        except Exception as e:
            raise OCRError(
                f"OCR gagal. PaddleOCR: {paddle_error} | Mistral fallback: {e}"
            )

    raise OCRError(f"OCR gagal. PaddleOCR: {paddle_error}")


# Backward-friendly alias.
def ocr_image(path_or_url: str, allow_mistral_fallback: bool = True) -> str:
    return ocr_file(path_or_url, allow_mistral_fallback=allow_mistral_fallback)
