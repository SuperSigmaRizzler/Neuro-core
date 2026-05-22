from config import (
    INSTANT_MODEL,
    INSTANT_PROVIDER,
    THINKING_MODEL,
    THINKING_PROVIDER
)
from providers.cloudflare import complete_cloudflare, stream_cloudflare
from providers.cerebras import complete_cerebras, stream_cerebras
from providers.gemini import complete_gemini, stream_gemini
from providers.groq import complete_groq, stream_groq


class RouterProviderError(Exception):
    pass


def get_provider_and_model(mode: str):
    mode = (mode or "instant").lower().strip()

    if mode == "thinking":
        return THINKING_PROVIDER, THINKING_MODEL

    return INSTANT_PROVIDER, INSTANT_MODEL


def stream_model_response(messages, mode: str):
    provider, model = get_provider_and_model(mode)
    provider = (provider or "groq").lower().strip()

    if provider == "groq":
        yield from stream_groq(messages, model=model)
        return

    if provider == "cerebras":
        yield from stream_cerebras(messages, model=model)
        return

    if provider == "gemini":
        yield from stream_gemini(messages, model=model)
        return

    if provider == "cloudflare":
        yield from stream_cloudflare(messages, model=model)
        return

    raise RouterProviderError(f"Provider belum didukung: {provider}")


def complete_model_response(messages, mode: str) -> str:
    provider, model = get_provider_and_model(mode)
    provider = (provider or "groq").lower().strip()

    if provider == "groq":
        return complete_groq(messages, model=model)

    if provider == "cerebras":
        return complete_cerebras(messages, model=model)

    if provider == "gemini":
        return complete_gemini(messages, model=model)

    if provider == "cloudflare":
        return complete_cloudflare(messages, model=model)

    raise RouterProviderError(f"Provider belum didukung: {provider}")
