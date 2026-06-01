import base64
import mimetypes
from pathlib import Path

import requests

from config import GEMINI_API_KEYS, MAX_PROVIDER_ATTEMPTS, REQUEST_TIMEOUT
from providers.key_utils import masked_secret, pick_attempt_keys


class GeminiProviderError(Exception):
    pass


def _extract_text(data) -> str:
    try:
        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )

        return "".join(part.get("text", "") for part in parts)

    except Exception:
        return ""


def _to_gemini_payload(messages, temperature=0.7):
    system_parts = []
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if not content:
            continue

        if role == "system":
            system_parts.append({"text": content})
            continue

        gemini_role = "model" if role == "assistant" else "user"

        contents.append({
            "role": gemini_role,
            "parts": [{"text": content}]
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "topP": 0.95
        }
    }

    if system_parts:
        payload["systemInstruction"] = {
            "parts": system_parts
        }

    return payload


def _post_gemini(key: str, model: str, payload: dict) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key
        },
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    if response.status_code >= 400:
        raise GeminiProviderError(
            f"Gemini error {response.status_code} with key {masked_secret(key)}: "
            f"{response.text[:800]}"
        )

    text = _extract_text(response.json())

    if not text:
        raise GeminiProviderError("Gemini response kosong.")

    return text


def stream_gemini(messages, model, temperature=0.7):
    keys = pick_attempt_keys(GEMINI_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise GeminiProviderError("GEMINI_API_KEYS / GEMINI_API_KEY belum diisi.")

    if not model:
        raise GeminiProviderError("Model Gemini belum diisi.")

    payload = _to_gemini_payload(messages, temperature=temperature)
    last_error = None

    for key in keys:
        try:
            text = _post_gemini(key, model, payload)
            yield text
            return

        except Exception as e:
            last_error = str(e)
            continue

    raise GeminiProviderError(last_error or "Semua Gemini key gagal.")


def complete_gemini(messages, model, temperature=0.7) -> str:
    keys = pick_attempt_keys(GEMINI_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise GeminiProviderError("GEMINI_API_KEYS / GEMINI_API_KEY belum diisi.")

    if not model:
        raise GeminiProviderError("Model Gemini belum diisi.")

    payload = _to_gemini_payload(messages, temperature=temperature)
    last_error = None

    for key in keys:
        try:
            return _post_gemini(key, model, payload)

        except Exception as e:
            last_error = str(e)
            continue

    raise GeminiProviderError(last_error or "Semua Gemini key gagal.")


def analyze_image_gemini(
    path: str,
    prompt: str = "Analyze this image clearly and answer the user's request.",
    model: str = "gemini-2.5-flash"
) -> str:
    keys = pick_attempt_keys(GEMINI_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise GeminiProviderError("GEMINI_API_KEYS / GEMINI_API_KEY belum diisi.")

    p = Path(path)

    if not p.exists():
        raise GeminiProviderError("File gambar tidak ditemukan.")

    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("utf-8")

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt or "Analyze this image clearly."
                    },
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": data
                        }
                    }
                ]
            }
        ]
    }

    last_error = None

    for key in keys:
        try:
            return _post_gemini(key, model, payload)

        except Exception as e:
            last_error = str(e)
            continue

    raise GeminiProviderError(last_error or "Semua Gemini Vision key gagal.")
