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
    Search/url/image stay false here because wrong tool use is worse than no tool use.
    Thinking can still upgrade for structurally complex messages.
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
        "needs_url_reading": False,
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

    needs_url_reading = _as_bool(
        data.get("needs_url_reading"),
        fallback.get("needs_url_reading", False)
    )

    wants_image_generation = _as_bool(
        data.get("wants_image_generation"),
        fallback.get("wants_image_generation", False)
    )

    # Image generation is above search/url reading.
    # If the user wants an image generated, do not search/open URLs unless
    # a future dedicated reference-image pipeline is explicitly added.
    if wants_image_generation:
        needs_search = False
        needs_url_reading = False

    return {
        "needs_thinking": bool(needs_thinking),
        "needs_search": bool(needs_search),
        "needs_url_reading": bool(needs_url_reading),
        "wants_image_generation": bool(wants_image_generation)
    }


def classify_user_intent(message: str) -> Dict:
    """
    Semantic intent classifier.
    Goal: human-like routing, not keyword-trigger routing.
    Search can be implicit, but must not override memory/context.
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
                    "You are NeuroMV's private intent router. "
                    "Return valid JSON only. Do not answer the user. "
                    "Use human semantic judgment, not a keyword checklist.\n\n"

                    "Core routing philosophy:\n"
                    "- First understand what the user is really trying to do.\n"
                    "- Do not require the user to explicitly say 'search', 'Google', or 'look it up'.\n"
                    "- If a normal helpful human would need current/public/external information to answer accurately, set needs_search=true.\n"
                    "- If the answer can be handled from memory, chat history, pasted logs/code, project context, or general reasoning, set needs_search=false.\n\n"

                    "Memory/context priority:\n"
                    "1. Questions about what just happened, what we were doing, previous debugging steps, current project state, "
                    "or 'lanjut tadi' must use memory/chat context, not search.\n"
                    "2. Jokes, emotional reactions, casual comments, or shared links used as examples should not trigger search or URL reading.\n"
                    "3. Coding/debugging with pasted logs/code usually needs reasoning, not search, unless the user asks about current docs/pricing/API changes.\n\n"

                    "Implicit search rules:\n"
                    "Set needs_search=true even without explicit search words when the user asks about:\n"
                    "- current or recently changing facts, prices, limits, policies, quotas, schedules, availability, or service status;\n"
                    "- how a public platform/service currently works, especially if timing or rules may change;\n"
                    "- official product docs or account/platform behavior that should be verified;\n"
                    "- examples: 'berapa lama link download export dikirim ke Gmail?', 'limit Groq sekarang gimana?', "
                    "'apakah OpenAI masih ada trial Plus?', 'harga API model ini berapa?', 'Railway trial masih berapa lama?'.\n\n"

                    "URL reading rules:\n"
                    "- Links/URLs are not automatically instructions to open them.\n"
                    "- Set needs_url_reading=true only when the user clearly wants the assistant to open, read, summarize, analyze, inspect, or use the URL content.\n"
                    "- If a URL is just part of a joke, example, chat context, citation-like text, or casual mention, needs_url_reading=false.\n"
                    "- WhatsApp/Telegram/social links should not be opened unless the user clearly asks to inspect the link itself.\n\n"

                    "Image generation rules:\n"
                    "- If the user asks to create, generate, draw, render, design, or visualize an image/poster/picture, set wants_image_generation=true.\n"
                    "- Image generation should suppress search/url reading unless the user clearly asks for web references first.\n\n"

                    "Thinking rules:\n"
                    "- needs_thinking is for reasoning depth, debugging complexity, multi-step planning, long code/logs, or careful analysis.\n"
                    "- needs_thinking is not the same as needs_search.\n\n"

                    "Return JSON exactly with these booleans:\n"
                    "{\n"
                    '  "needs_thinking": true/false,\n'
                    '  "needs_search": true/false,\n'
                    '  "needs_url_reading": true/false,\n'
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
