import json
import re
from typing import Dict


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


def _fallback_intent(message: str) -> Dict:
    """
    Fallback tanpa daftar pemicu.
    Ini cuma menilai struktur umum pesan, bukan kata tertentu.
    """
    text = message or ""

    needs_thinking = (
        len(text) > 450
        or "```" in text
        or text.count("\n") >= 4
        or text.count("?") >= 3
    )

    return {
        "needs_thinking": needs_thinking,
        "needs_search": False,
        "wants_image_generation": False
    }


def classify_user_intent(message: str) -> Dict:
    """
    Uses the model's judgment to classify intent.
    No trigger-word list.
    If classifier fails, fallback only uses message structure.
    """
    message = (message or "").strip()

    fallback = _fallback_intent(message)

    if not message:
        return fallback

    try:
        from providers.router import complete_model_response

        classifier_messages = [
            {
                "role": "system",
                "content": (
                    "You are an intent classifier for an AI assistant app. "
                    "Use semantic judgment, not trigger words. "
                    "Return valid JSON only. "
                    "Classify whether the user's message needs careful reasoning, needs fresh/current web information, "
                    "or is asking the assistant to create/generate an image. "
                    "Do not answer the user. Do not add explanations."
                )
            },
            {
                "role": "user",
                "content": (
                    "Classify this message into JSON with exactly these boolean fields:\n"
                    "{\n"
                    '  "needs_thinking": true/false,\n'
                    '  "needs_search": true/false,\n'
                    '  "wants_image_generation": true/false\n'
                    "}\n\n"
                    f"Message:\n{message}"
                )
            }
        ]

        raw = complete_model_response(classifier_messages, "instant")
        data = _json_from_text(raw)

        return {
            "needs_thinking": bool(data.get("needs_thinking", fallback["needs_thinking"])),
            "needs_search": bool(data.get("needs_search", fallback["needs_search"])),
            "wants_image_generation": bool(data.get("wants_image_generation", fallback["wants_image_generation"]))
        }

    except Exception:
        return fallback


def choose_runtime_mode(user_selected_mode: str, message: str, intent: Dict | None = None) -> str:
    selected = (user_selected_mode or "instant").lower().strip()
    intent = intent or _fallback_intent(message)

    if selected == "thinking":
        return "thinking"

    if intent.get("needs_thinking"):
        return "thinking"

    return "instant"
