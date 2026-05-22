import json
from typing import Dict, Iterable, Optional

import requests

from config import REQUEST_TIMEOUT
from providers.key_utils import masked_secret


class OpenAICompatError(Exception):
    pass


def stream_openai_compat(
    *,
    provider_name: str,
    base_url: str,
    api_key: str,
    messages,
    model: str,
    temperature: float = 0.7,
    extra_headers: Optional[Dict] = None,
    extra_payload: Optional[Dict] = None,
):
    if not api_key:
        raise OpenAICompatError(f"{provider_name}: API key kosong.")

    if not model:
        raise OpenAICompatError(f"{provider_name}: model kosong.")

    url = base_url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.95,
        "stream": True
    }

    if extra_payload:
        payload.update(extra_payload)

    try:
        with requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=REQUEST_TIMEOUT
        ) as response:
            if response.status_code >= 400:
                raise OpenAICompatError(
                    f"{provider_name} error {response.status_code} "
                    f"with key {masked_secret(api_key)}: {response.text[:800]}"
                )

            for raw_line in response.iter_lines():
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="ignore").strip()

                if not line.startswith("data: "):
                    continue

                data = line.replace("data: ", "", 1).strip()

                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    text = delta.get("content", "")

                    if text:
                        yield text

                except Exception:
                    continue

    except requests.exceptions.Timeout:
        raise OpenAICompatError(
            f"{provider_name}: timeout with key {masked_secret(api_key)}."
        )

    except requests.exceptions.RequestException as e:
        raise OpenAICompatError(
            f"{provider_name}: request gagal with key {masked_secret(api_key)}: {e}"
        )


def complete_openai_compat(
    *,
    provider_name: str,
    base_url: str,
    api_key: str,
    messages,
    model: str,
    temperature: float = 0.7,
    extra_headers: Optional[Dict] = None,
    extra_payload: Optional[Dict] = None,
) -> str:
    if not api_key:
        raise OpenAICompatError(f"{provider_name}: API key kosong.")

    if not model:
        raise OpenAICompatError(f"{provider_name}: model kosong.")

    url = base_url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.95,
        "stream": False
    }

    if extra_payload:
        payload.update(extra_payload)

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code >= 400:
            raise OpenAICompatError(
                f"{provider_name} error {response.status_code} "
                f"with key {masked_secret(api_key)}: {response.text[:800]}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        raise OpenAICompatError(
            f"{provider_name}: timeout with key {masked_secret(api_key)}."
        )

    except requests.exceptions.RequestException as e:
        raise OpenAICompatError(
            f"{provider_name}: request gagal with key {masked_secret(api_key)}: {e}"
        )

    except Exception as e:
        raise OpenAICompatError(
            f"{provider_name}: response parse gagal with key {masked_secret(api_key)}: {e}"
        )
