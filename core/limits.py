from typing import Dict

from config import (
    DAILY_LIMIT,
    FILE_LIMIT,
    IMAGE_LIMIT,
    OCR_LIMIT,
    SEARCH_LIMIT,
    UPLOAD_LIMIT,
    URL_LIMIT,
    VISION_LIMIT
)
from core.db import check_and_increment_usage


LIMIT_MAP = {
    "chat": DAILY_LIMIT,
    "upload": UPLOAD_LIMIT,
    "file": FILE_LIMIT,
    "image": IMAGE_LIMIT,
    "search": SEARCH_LIMIT,
    "url": URL_LIMIT,
    "ocr": OCR_LIMIT,
    "vision": VISION_LIMIT
}


class LimitError(Exception):
    def __init__(self, message: str, info: Dict):
        super().__init__(message)
        self.info = info


def check_limit(user_key: str, kind: str) -> Dict:
    limit = LIMIT_MAP.get(kind)

    if limit is None:
        limit = DAILY_LIMIT

    result = check_and_increment_usage(user_key, kind, limit)

    if not result["ok"]:
        raise LimitError(
            f"{kind} limit reached ({result['count']}/{result['limit']} per day).",
            result
        )

    return result


def format_limit_error(error: LimitError) -> str:
    # User-facing message only.
    # Do not expose exact daily limits/counts in UI.
    return "You've reached your usage limit. Please try again later."
