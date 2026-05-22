import requests

from config import (
    MAX_CONTEXT_CHARS,
    MAX_PROVIDER_ATTEMPTS,
    REQUEST_TIMEOUT,
    SERPAPI_API_KEYS,
    SERPER_API_KEYS,
    TAVILY_API_KEYS
)
from core.utils import safe_truncate
from providers.key_utils import masked_secret, pick_attempt_keys


class WebSearchError(Exception):
    pass


def _normalize_results(provider: str, items):
    results = []

    for item in items or []:
        title = item.get("title") or item.get("name") or ""
        url = item.get("link") or item.get("url") or item.get("href") or ""
        snippet = (
            item.get("snippet")
            or item.get("content")
            or item.get("description")
            or item.get("body")
            or ""
        )

        if title or url or snippet:
            results.append({
                "provider": provider,
                "title": title,
                "url": url,
                "snippet": snippet
            })

    return results


def _search_tavily(query: str, max_results: int = 5):
    keys = pick_attempt_keys(TAVILY_API_KEYS, MAX_PROVIDER_ATTEMPTS)
    last_error = None

    for key in keys:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}"
                },
                json={
                    "query": query,
                    "topic": "general",
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False
                },
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code >= 400:
                last_error = (
                    f"Tavily error {response.status_code} "
                    f"with key {masked_secret(key)}: {response.text[:300]}"
                )
                continue

            data = response.json()
            return _normalize_results("tavily", data.get("results", []))

        except Exception as e:
            last_error = f"Tavily gagal with key {masked_secret(key)}: {e}"
            continue

    if keys:
        raise WebSearchError(last_error or "Tavily gagal.")

    return []


def _search_serper(query: str, max_results: int = 5):
    keys = pick_attempt_keys(SERPER_API_KEYS, MAX_PROVIDER_ATTEMPTS)
    last_error = None

    for key in keys:
        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": key
                },
                json={
                    "q": query,
                    "num": max_results
                },
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code >= 400:
                last_error = (
                    f"Serper error {response.status_code} "
                    f"with key {masked_secret(key)}: {response.text[:300]}"
                )
                continue

            data = response.json()
            return _normalize_results("serper", data.get("organic", []))

        except Exception as e:
            last_error = f"Serper gagal with key {masked_secret(key)}: {e}"
            continue

    if keys:
        raise WebSearchError(last_error or "Serper gagal.")

    return []


def _search_serpapi(query: str, max_results: int = 5):
    keys = pick_attempt_keys(SERPAPI_API_KEYS, MAX_PROVIDER_ATTEMPTS)
    last_error = None

    for key in keys:
        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google",
                    "q": query,
                    "api_key": key,
                    "num": max_results
                },
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code >= 400:
                last_error = (
                    f"SerpAPI error {response.status_code} "
                    f"with key {masked_secret(key)}: {response.text[:300]}"
                )
                continue

            data = response.json()
            return _normalize_results("serpapi", data.get("organic_results", []))

        except Exception as e:
            last_error = f"SerpAPI gagal with key {masked_secret(key)}: {e}"
            continue

    if keys:
        raise WebSearchError(last_error or "SerpAPI gagal.")

    return []


def search_web(query: str, max_results: int = 5):
    errors = []

    for fn in [_search_tavily, _search_serper, _search_serpapi]:
        try:
            results = fn(query, max_results=max_results)

            if results:
                return results[:max_results]

        except Exception as e:
            errors.append(str(e))
            continue

    if errors:
        raise WebSearchError("Semua search provider gagal: " + " | ".join(errors))

    raise WebSearchError("Tidak ada search API key yang aktif.")


def format_search_results(query: str, results) -> str:
    lines = [f"Search query: {query}", ""]

    for i, item in enumerate(results or [], start=1):
        lines.append(
            f"{i}. {item.get('title', '')}\n"
            f"Provider: {item.get('provider', '')}\n"
            f"URL: {item.get('url', '')}\n"
            f"Snippet: {item.get('snippet', '')}"
        )

    return safe_truncate("\n\n".join(lines), MAX_CONTEXT_CHARS)
