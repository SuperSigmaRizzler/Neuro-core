from pathlib import Path

from config import MAX_CONTEXT_CHARS, TEXT_EXTS
from core.utils import safe_truncate


class FileReadError(Exception):
    pass


def is_text_file(path: str) -> bool:
    return Path(path).suffix.lower() in TEXT_EXTS


def read_text_file(path: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    p = Path(path)

    if not p.exists():
        raise FileReadError("File tidak ditemukan.")

    if p.suffix.lower() not in TEXT_EXTS:
        raise FileReadError("Jenis file ini belum didukung sebagai text file.")

    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        raise FileReadError(f"Gagal membaca file: {e}")

    return safe_truncate(text, max_chars)


def read_supported_textlike_file(path: str, original_name: str = "") -> str:
    content = read_text_file(path)
    label = original_name or Path(path).name

    return f"Uploaded text file: {label}\n\n{content}"
