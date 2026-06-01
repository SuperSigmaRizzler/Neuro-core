from config import (
    CLOUDFLARE_ACCOUNT_IDS,
    CLOUDFLARE_API_TOKENS,
    MAX_PROVIDER_ATTEMPTS
)
from providers.key_utils import cloudflare_pairs
from providers.openai_compat import OpenAICompatError, complete_openai_compat, stream_openai_compat


class CloudflareProviderError(Exception):
    pass


def _base_url(account_id: str) -> str:
    return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"


def stream_cloudflare(messages, model, temperature=0.7):
    pairs = cloudflare_pairs(
        CLOUDFLARE_ACCOUNT_IDS,
        CLOUDFLARE_API_TOKENS,
        MAX_PROVIDER_ATTEMPTS
    )

    if not pairs:
        raise CloudflareProviderError(
            "CLOUDFLARE_ACCOUNT_IDS/CLOUDFLARE_ACCOUNT_ID dan "
            "CLOUDFLARE_API_TOKENS/CLOUDFLARE_API_TOKEN belum diisi."
        )

    last_error = None

    for account_id, token in pairs:
        try:
            yield from stream_openai_compat(
                provider_name="Cloudflare Workers AI",
                base_url=_base_url(account_id),
                api_key=token,
                messages=messages,
                model=model,
                temperature=temperature
            )
            return

        except OpenAICompatError as e:
            last_error = str(e)
            continue

    raise CloudflareProviderError(last_error or "Semua Cloudflare account/token gagal.")


def complete_cloudflare(messages, model, temperature=0.7) -> str:
    pairs = cloudflare_pairs(
        CLOUDFLARE_ACCOUNT_IDS,
        CLOUDFLARE_API_TOKENS,
        MAX_PROVIDER_ATTEMPTS
    )

    if not pairs:
        raise CloudflareProviderError(
            "CLOUDFLARE_ACCOUNT_IDS/CLOUDFLARE_ACCOUNT_ID dan "
            "CLOUDFLARE_API_TOKENS/CLOUDFLARE_API_TOKEN belum diisi."
        )

    last_error = None

    for account_id, token in pairs:
        try:
            return complete_openai_compat(
                provider_name="Cloudflare Workers AI",
                base_url=_base_url(account_id),
                api_key=token,
                messages=messages,
                model=model,
                temperature=temperature
            )

        except OpenAICompatError as e:
            last_error = str(e)
            continue

    raise CloudflareProviderError(last_error or "Semua Cloudflare account/token gagal.")
