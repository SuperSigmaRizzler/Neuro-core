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


def _as_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    if isinstance(value, (int, float)):
        return bool(value)

    raw = str(value).strip().lower()

    if raw in {"true", "yes", "y", "1", "on"}:
        return True

    if raw in {"false", "no", "n", "0", "off"}:
        return False

    return default


def _fallback_intent(message: str) -> Dict:
    """
    Safe fallback.
    No search/image guess here, because wrong search is more annoying than no search.
    Thinking may upgrade for long/complex structure.
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


def _normalize_intent(data: Dict, fallback: Dict) -> Dict:
    needs_thinking = _as_bool(
        data.get("needs_thinking"),
        fallback.get("needs_thinking", False)
    )

    needs_search = _as_bool(
        data.get("needs_search"),
        fallback.get("needs_search", False)
    )

    wants_image_generation = _as_bool(
        data.get("wants_image_generation"),
        fallback.get("wants_image_generation", False)
    )

    # Image generation is above search in NeuroMV's routing.
    # If the user wants an image, do not search unless a future dedicated
    # pipeline explicitly adds reference-search. Current app should generate.
    if wants_image_generation:
        needs_search = False

    return {
        "needs_thinking": bool(needs_thinking),
        "needs_search": bool(needs_search),
        "wants_image_generation": bool(wants_image_generation)
    }


def classify_user_intent(message: str) -> Dict:
    """
    Semantic intent classifier.
    Memory/context is preferred over search. Search is last-resort only.
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
                    "You are NeuroMV's private intent classifier. "
                    "Return valid JSON only. Do not answer the user. "
                    "Use semantic judgment, not a keyword checklist.\n\n"

                    "Routing priority:\n"
                    "1. Prefer memory, chat history, project context, and the current conversation.\n"
                    "2. If the user is asking about what just happened, what was done earlier, saved context, "
                    "their project, pasted logs/code, or a continuation of the current work, needs_search must be false.\n"
                    "3. If the user asks for image creation, drawing, rendering, poster/design generation, or visual generation, "
                    "wants_image_generation must be true and needs_search must be false.\n"
                    "4. Search is the final layer only. needs_search should be true only when the answer genuinely depends on "
                    "fresh/current outside information or the user explicitly wants the web/current lookup.\n"
                    "5. Do not use search for coding/debugging when the user already provided logs/code. Use reasoning instead.\n"
                    "6. Do not use search for personal/project memory questions. Use context instead.\n"
                    "7. needs_thinking is about reasoning depth, not web search.\n\n"

                    "Return JSON exactly with these booleans:\n"
                    "{\n"
                    '  "needs_thinking": true/false,\n'
                    '  "needs_search": true/false,\n'
                    '  "wants_image_generation": true/false\n'
                    "}"
                )
            },
            {
                "role": "user",
                "content": (
                    "Classify this user message for NeuroMV routing.\n\n"
                    f"Message:\n{message}"
                )
            }
        ]

        raw = complete_model_response(classifier_messages, "instant")
        data = _json_from_text(raw)

        if not isinstance(data, dict):
            return fallback

        return _normalize_intent(data, fallback)

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
