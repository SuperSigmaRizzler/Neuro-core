import hashlib
import secrets
from pathlib import Path
from werkzeug.utils import secure_filename

from config import ALLOWED_UPLOAD_EXTS, MAX_UPLOAD_BYTES, UPLOAD_DIR
from core.utils import ensure_dir, filename_ext


class UploadSecurityError(Exception):
    pass


def make_guest_id() -> str:
    return "guest_" + secrets.token_hex(16)


def hash_stable(value: str, length: int = 32) -> str:
    raw = str(value or "").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def validate_upload(filename: str, size_bytes: int | None = None) -> None:
    ext = filename_ext(filename)

    if not filename:
        raise UploadSecurityError("File tidak punya nama.")

    if ext not in ALLOWED_UPLOAD_EXTS:
        raise UploadSecurityError(f"Jenis file {ext or '(no extension)'} belum didukung.")

    if size_bytes is not None and size_bytes > MAX_UPLOAD_BYTES:
        mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise UploadSecurityError(f"File terlalu besar. Maksimal {mb} MB.")


def build_safe_upload_path(original_name: str) -> tuple[str, str]:
    ensure_dir(UPLOAD_DIR)

    safe_name = secure_filename(original_name or "upload.bin")
    ext = filename_ext(safe_name)

    token = secrets.token_hex(16)
    stored_name = f"{token}{ext}"
    path = str(Path(UPLOAD_DIR) / stored_name)

    return path, stored_name
