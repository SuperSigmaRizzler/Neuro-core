from config import GROQ_API_KEYS, MAX_PROVIDER_ATTEMPTS
from providers.key_utils import pick_attempt_keys
from providers.openai_compat import OpenAICompatError, complete_openai_compat, stream_openai_compat


GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProviderError(Exception):
    pass


def stream_groq(messages, model, temperature=0.7):
    keys = pick_attempt_keys(GROQ_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise GroqProviderError("GROQ_API_KEYS / GROQ_API_KEY belum diisi.")

    last_error = None

    for key in keys:
        try:
            yield from stream_openai_compat(
                provider_name="Groq",
                base_url=GROQ_BASE_URL,
                api_key=key,
                messages=messages,
                model=model,
                temperature=temperature
            )
            return

        except OpenAICompatError as e:
            last_error = str(e)
            continue

    raise GroqProviderError(last_error or "Semua Groq key gagal.")


def complete_groq(messages, model, temperature=0.7) -> str:
    keys = pick_attempt_keys(GROQ_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise GroqProviderError("GROQ_API_KEYS / GROQ_API_KEY belum diisi.")

    last_error = None

    for key in keys:
        try:
            return complete_openai_compat(
                provider_name="Groq",
                base_url=GROQ_BASE_URL,
                api_key=key,
                messages=messages,
                model=model,
                temperature=temperature
            )

        except OpenAICompatError as e:
            last_error = str(e)
            continue

    raise GroqProviderError(last_error or "Semua Groq key gagal.")
