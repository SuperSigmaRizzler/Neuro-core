import math
import re


PUBLIC_BACKEND_ERROR = (
    "NeuroMV sedang gagal memproses request ini. "
    "Coba lagi sebentar lagi, atau cek server log lokal jika kamu sedang debugging."
)


def _entropy(s: str) -> float:
    if not s:
        return 0.0

    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1

    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def _looks_like_secret_value(value: str) -> bool:
    value = str(value or "").strip()

    if len(value) < 24:
        return False

    # Secret-like values are usually long, compact, and high-entropy.
    compact = re.fullmatch(r"[A-Za-z0-9_\-./+=:]{24,}", value) is not None
    return compact and _entropy(value) >= 3.4


def sanitize_for_model(text: str) -> str:
    """
    Data firewall only.

    This does not decide intent.
    This does not route behavior.
    This does not produce refusal text.

    It only prevents secret-like values from being sent to the model.
    """
    text = str(text or "")

    parts = re.split(r"(\s+)", text)
    safe_parts = []

    for part in parts:
        safe_parts.append("[REDACTED_SECRET]" if _looks_like_secret_value(part) else part)

    text = "".join(safe_parts)

    # Redact common env assignment values without using this as intent routing.
    text = re.sub(
        r"(?i)([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PRIVATE)[A-Z0-9_]*\s*=\s*)([^\s]+)",
        lambda m: m.group(1) + "[REDACTED_SECRET]",
        text
    )

    return text


def sanitize_public_error(error) -> str:
    """
    Public UI error boundary.
    Raw backend/provider errors stay in server logs only.
    """
    return PUBLIC_BACKEND_ERROR
