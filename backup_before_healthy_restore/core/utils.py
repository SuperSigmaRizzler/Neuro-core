import json
import os
import re
import time
from pathlib import Path
from typing import Any


def ensure_parent(path: str) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_json(path: str, default: Any):
    try:
        if not os.path.exists(path):
            ensure_parent(path)
            save_json(path, default)
            return default

        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
            if not text:
                return default
            return json.loads(text)

    except Exception:
        return default


def save_json(path: str, data: Any) -> None:
    ensure_parent(path)
    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(temp_path, path)


def now_ts() -> int:
    return int(time.time())


def today_key() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def safe_truncate(text: str, max_chars: int) -> str:
    text = str(text or "")

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + "\n\n[Content truncated]"


def clean_spaces(text: str) -> str:
    return " ".join(str(text or "").split()).strip()


def filename_ext(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def human_size(size_bytes: int) -> str:
    try:
        size = float(size_bytes)
    except Exception:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]

    for unit in units:
        if size < 1024:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} TB"


def normalize_user_key(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(r"[^A-Za-z0-9:_-]", "_", value)
    return value[:120] or "guest:unknown"
