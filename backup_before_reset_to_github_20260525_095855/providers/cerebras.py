from config import CEREBRAS_API_KEYS, MAX_PROVIDER_ATTEMPTS
from providers.key_utils import pick_attempt_keys
from providers.openai_compat import OpenAICompatError, complete_openai_compat, stream_openai_compat


CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"


class CerebrasProviderError(Exception):
    pass


def stream_cerebras(messages, model, temperature=0.7):
    keys = pick_attempt_keys(CEREBRAS_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise CerebrasProviderError("CEREBRAS_API_KEYS / CEREBRAS_API_KEY belum diisi.")

    last_error = None

    for key in keys:
        try:
            yield from stream_openai_compat(
                provider_name="Cerebras",
                base_url=CEREBRAS_BASE_URL,
                api_key=key,
                messages=messages,
                model=model,
                temperature=temperature
            )
            return

        except OpenAICompatError as e:
            last_error = str(e)
            continue

    raise CerebrasProviderError(last_error or "Semua Cerebras key gagal.")


def complete_cerebras(messages, model, temperature=0.7) -> str:
    keys = pick_attempt_keys(CEREBRAS_API_KEYS, MAX_PROVIDER_ATTEMPTS)

    if not keys:
        raise CerebrasProviderError("CEREBRAS_API_KEYS / CEREBRAS_API_KEY belum diisi.")

    last_error = None

    for key in keys:
        try:
            return complete_openai_compat(
                provider_name="Cerebras",
                base_url=CEREBRAS_BASE_URL,
                api_key=key,
                messages=messages,
                model=model,
                temperature=temperature
            )

        except OpenAICompatError as e:
            last_error = str(e)
            continue

    raise CerebrasProviderError(last_error or "Semua Cerebras key gagal.")
