import re
from typing import Dict, List, Optional

from core.db import add_assistant_lesson, format_lessons_for_prompt, get_assistant_lessons
from core.utils import clean_spaces


CORRECTION_PATTERNS = [
    r"\bsalah\b",
    r"\bkeliru\b",
    r"\bnggak begitu\b",
    r"\bga begitu\b",
    r"\bbukan begitu\b",
    r"\bseharusnya\b",
    r"\bharusnya\b",
    r"\bjangan .* lagi\b",
    r"\bnext time\b",
    r"\bingat\b",
    r"\bremember\b",
    r"\bkoreksi\b",
    r"\bfix cara kamu\b",
    r"\bkamu lupa\b",
    r"\bkok .* hilang\b",
    r"\bfitur lama\b",
]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{12,}",
    r"gsk_[A-Za-z0-9_-]{12,}",
    r"AIza[A-Za-z0-9_-]{20,}",
    r"api[_ -]?key\s*[:=]",
    r"password\s*[:=]",
    r"secret\s*[:=]",
    r"token\s*[:=]",
    r"bearer\s+[A-Za-z0-9._-]+",
]


def looks_like_correction(text: str) -> bool:
    lowered = (text or "").lower()

    return any(re.search(pattern, lowered) for pattern in CORRECTION_PATTERNS)


def contains_secret_like_text(text: str) -> bool:
    lowered = text or ""

    return any(re.search(pattern, lowered, re.IGNORECASE) for pattern in SECRET_PATTERNS)


def extract_lesson_from_correction(user_text: str, assistant_text: str = "") -> Optional[str]:
    text = clean_spaces(user_text)

    if not text:
        return None

    if contains_secret_like_text(text):
        return None

    if not looks_like_correction(text):
        return None

    # Keep it compact and useful. Do not store whole long chats.
    lesson = text

    prefixes = [
        "salah,",
        "salah.",
        "nggak begitu,",
        "ga begitu,",
        "bukan begitu,",
        "koreksi:",
        "ingat:",
        "remember:",
    ]

    lowered = lesson.lower()

    for prefix in prefixes:
        if lowered.startswith(prefix):
            lesson = lesson[len(prefix):].strip()
            break

    # Convert into a durable instruction-style lesson.
    lesson = clean_spaces(lesson)

    if not lesson:
        return None

    if len(lesson) < 8:
        return None

    if len(lesson) > 700:
        lesson = lesson[:700].rstrip() + "..."

    return f"Correction learned: {lesson}"


def maybe_store_lesson(
    *,
    user_key: str,
    user_text: str,
    assistant_text: str = "",
    chat_id: Optional[str] = None
) -> Optional[Dict]:
    lesson = extract_lesson_from_correction(user_text, assistant_text)

    if not lesson:
        return None

    return add_assistant_lesson(
        user_key=user_key,
        lesson=lesson,
        source_text=user_text,
        chat_id=chat_id,
        importance=3
    )


def lessons_prompt_context(user_key: str, chat_id: Optional[str] = None, limit: int = 12) -> str:
    lessons = get_assistant_lessons(user_key, chat_id=chat_id, limit=limit)
    return format_lessons_for_prompt(lessons)
