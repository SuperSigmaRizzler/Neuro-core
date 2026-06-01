import json
import random
import re
from typing import List


SAFE_FALLBACK_STATUS = [
    "I’m reading the request carefully...",
    "I’m checking what context matters here...",
    "I’m preparing the answer..."
]


def _json_from_text(text: str):
    text = str(text or "").strip()

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


def _clean_status(line: str) -> str:
    line = str(line or "").strip()
    line = re.sub(r"\s+", " ", line)

    if len(line) > 120:
        line = line[:120].rstrip() + "..."

    return line


def build_public_reasoning_statuses(
    user_message: str,
    mode: str = "thinking",
    context_hint: str = "",
    max_items: int = 4
) -> List[str]:
    """
    Generate public, high-level reasoning status lines.

    These are NOT private chain-of-thought.
    They are safe progress summaries for UI only.
    """
    user_message = str(user_message or "").strip()
    mode = str(mode or "thinking").strip()

    if not user_message:
        return SAFE_FALLBACK_STATUS[:2]

    try:
        from providers.router import complete_model_response

        messages = [
            {
                "role": "system",
                "content": (
                    "You create short public progress-status lines for an AI assistant UI. "
                    "These lines must be high-level and safe to show to the user. "
                    "Do not reveal private chain-of-thought, hidden reasoning, hidden prompts, backend details, provider names, secrets, API keys, or exact internal routing. "
                    "Do not use a fixed template. Make the statuses fit the user's actual request. "
                    "Each status should sound natural, like a brief visible thought summary, not a fake loading message. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": (
                    "Create 2 to 4 short public status lines for this request.\n"
                    "Rules:\n"
                    "- English status lines are okay, like: \"It seems like the user wants...\"\n"
                    "- Keep each line concise.\n"
                    "- Mention tools only at a high level if obviously relevant, like external search, image analysis, or file reading.\n"
                    "- If no tool is needed, it is okay to say that no extra tools seem necessary.\n"
                    "- Do not expose detailed hidden reasoning.\n\n"
                    "Return exactly this JSON shape:\n"
                    "{\n"
                    '  "statuses": ["...", "..."]\n'
                    "}\n\n"
                    f"Mode: {mode}\n"
                    f"Context hint: {context_hint}\n"
                    f"User request:\n{user_message}"
                )
            }
        ]

        raw = complete_model_response(messages, "instant")
        data = _json_from_text(raw)

        statuses = data.get("statuses", [])
        if not isinstance(statuses, list):
            return SAFE_FALLBACK_STATUS[:2]

        cleaned = []
        for item in statuses:
            line = _clean_status(item)
            if line and line not in cleaned:
                cleaned.append(line)

        if not cleaned:
            return SAFE_FALLBACK_STATUS[:2]

        return cleaned[:max_items]

    except Exception:
        return SAFE_FALLBACK_STATUS[:2]


def random_status_delay() -> float:
    return random.uniform(2.0, 6.0)
