import json
import re
from typing import Dict, List, Optional

from core.db import add_assistant_lesson, format_lessons_for_prompt, get_assistant_lessons
from core.utils import clean_spaces


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


def contains_secret_like_text(text: str) -> bool:
    return any(re.search(pattern, text or "", re.IGNORECASE) for pattern in SECRET_PATTERNS)


def _json_from_text(text: str) -> Dict:
    text = (text or "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _as_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    raw = str(value).strip().lower()

    if raw in {"true", "yes", "1", "on"}:
        return True

    if raw in {"false", "no", "0", "off"}:
        return False

    return default


def classify_learning_semantically(user_text: str, assistant_text: str = "") -> Dict:
    """
    Semantic learning classifier.
    This decides by meaning, not trigger words.
    If it fails, NeuroMV learns nothing instead of guessing.
    """
    user_text = clean_spaces(user_text)
    assistant_text = clean_spaces(assistant_text)

    fallback = {
        "should_learn": False,
        "is_global": False,
        "lesson": ""
    }

    if not user_text:
        return fallback

    if contains_secret_like_text(user_text):
        return fallback

    try:
        from providers.router import complete_model_response

        messages = [
            {
                "role": "system",
                "content": (
                    "You are NeuroMV's private memory-learning classifier. "
                    "Return valid JSON only. Do not answer the user.\n\n"

                    "Decide semantically whether the user's message should become a durable memory/lesson.\n"
                    "Do not use keyword matching. Understand the user's intent.\n\n"

                    "Learn ONLY when the user is giving a durable correction, preference, instruction, project rule, "
                    "or future behavior expectation that should affect later responses.\n\n"

                    "Do NOT learn ordinary questions, jokes, emotional reactions, temporary debugging messages, "
                    "or questions asking whether the assistant remembers something.\n\n"

                    "Use is_global=true when the lesson should apply across chats, such as long-term coding preferences, "
                    "NeuroMV project rules, communication style, memory behavior, safety preferences, or future instructions.\n"
                    "Use is_global=false only when the correction is clearly specific to this current chat/task.\n\n"

                    "The lesson must be concise, safe, and written as an instruction for future NeuroMV behavior.\n"
                    "Never store passwords, API keys, tokens, secrets, or private credentials.\n\n"

                    "Return exactly:\n"
                    "{\n"
                    '  "should_learn": true/false,\n'
                    '  "is_global": true/false,\n'
                    '  "lesson": "short safe lesson or empty string"\n'
                    "}"
                )
            },
            {
                "role": "user",
                "content": (
                    "User message:\n"
                    f"{user_text}\n\n"
                    "Assistant response, if available:\n"
                    f"{assistant_text}"
                )
            }
        ]

        raw = complete_model_response(messages, "instant")
        data = _json_from_text(raw)

        should_learn = _as_bool(data.get("should_learn"), False)
        is_global = _as_bool(data.get("is_global"), False)
        lesson = clean_spaces(data.get("lesson", ""))

        if not should_learn:
            return fallback

        if not lesson or len(lesson) < 8:
            return fallback

        if contains_secret_like_text(lesson):
            return fallback

        if len(lesson) > 700:
            lesson = lesson[:700].rstrip() + "..."

        return {
            "should_learn": True,
            "is_global": bool(is_global),
            "lesson": f"Correction learned: {lesson}"
        }

    except Exception:
        return fallback


def extract_lesson_from_correction(user_text: str, assistant_text: str = "") -> Optional[str]:
    result = classify_learning_semantically(user_text, assistant_text)

    if not result.get("should_learn"):
        return None

    return result.get("lesson") or None


def maybe_store_lesson(
    *,
    user_key: str,
    user_text: str,
    assistant_text: str = "",
    chat_id: Optional[str] = None
) -> Optional[Dict]:
    result = classify_learning_semantically(user_text, assistant_text)

    if not result.get("should_learn"):
        return None

    lesson = result.get("lesson") or ""

    if not lesson:
        return None

    target_chat_id = None if result.get("is_global") else chat_id

    return add_assistant_lesson(
        user_key=user_key,
        lesson=lesson,
        source_text=user_text,
        chat_id=target_chat_id,
        importance=3
    )


def lessons_prompt_context(user_key: str, chat_id: Optional[str] = None, limit: int = 12) -> str:
    lessons = get_assistant_lessons(user_key, chat_id=chat_id, limit=limit)
    return format_lessons_for_prompt(lessons)
