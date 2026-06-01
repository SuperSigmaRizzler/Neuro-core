import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import MAX_CONTEXT_CHARS, REQUEST_TIMEOUT
from core.utils import safe_truncate


URL_RE = re.compile(r"https?://[^\s<>\")\]]+")


class URLReadError(Exception):
    pass


def extract_urls(text: str):
    urls = URL_RE.findall(text or "")

    clean = []

    for url in urls:
        url = url.rstrip(".,;:!?)]}")
        if url not in clean:
            clean.append(url)

    return clean


def is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
    except Exception:
        return False


def read_url(url: str, timeout: int | None = None, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if not is_valid_http_url(url):
        raise URLReadError("URL tidak valid.")

    response = requests.get(
        url,
        timeout=timeout or min(REQUEST_TIMEOUT, 25),
        headers={
            "User-Agent": "Mozilla/5.0 NeuroMV/1.0"
        }
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" not in content_type and "application/xhtml" not in content_type:
        text = response.text
        return safe_truncate(
            f"URL: {url}\nContent-Type: {content_type}\n\n{text}",
            max_chars
        )

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_description = ""

    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_description = meta.get("content", "").strip()

    text = "\n".join(
        line.strip()
        for line in soup.get_text("\n").splitlines()
        if line.strip()
    )

    result = f"Title: {title}\nURL: {url}\nDescription: {meta_description}\n\nContent:\n{text}"

    return safe_truncate(result, max_chars)
