from pathlib import Path
from typing import Dict, List, Optional

from config import IMAGE_EXTS, MAX_CONTEXT_CHARS, PDF_EXTS
from core.utils import safe_truncate
from tools.file_reader import is_text_file, read_supported_textlike_file
from tools.image_reader import analyze_image
from tools.pdf_reader import read_pdf
from tools.url_reader import extract_urls, read_url
from tools.web_search import format_search_results, search_web


class ContextToolError(Exception):
    pass


def read_uploaded_file_context(
    *,
    path: str,
    original_name: str,
    user_message: str = ""
) -> Dict:
    suffix = Path(path).suffix.lower()

    if suffix in PDF_EXTS:
        try:
            return {
                "kind": "pdf",
                "status": "reading_pdf",
                "label": original_name,
                "content": f"[UPLOADED PDF: {original_name}]\n{read_pdf(path)}"
            }
        except Exception as e:
            return {
                "kind": "pdf",
                "status": "reading_pdf",
                "label": original_name,
                "content": f"[PDF READ ERROR: {original_name}]\n{e}"
            }

    if suffix in IMAGE_EXTS:
        try:
            return {
                "kind": "image",
                "status": "analyzing_image",
                "label": original_name,
                "content": f"[UPLOADED IMAGE: {original_name}]\n{analyze_image(path, user_message)}"
            }
        except Exception as e:
            return {
                "kind": "image",
                "status": "analyzing_image",
                "label": original_name,
                "content": f"[IMAGE ANALYSIS ERROR: {original_name}]\n{e}"
            }

    if is_text_file(path):
        try:
            return {
                "kind": "file",
                "status": "reading_file",
                "label": original_name,
                "content": f"[UPLOADED TEXT FILE: {original_name}]\n{read_supported_textlike_file(path, original_name)}"
            }
        except Exception as e:
            return {
                "kind": "file",
                "status": "reading_file",
                "label": original_name,
                "content": f"[TEXT FILE READ ERROR: {original_name}]\n{e}"
            }

    return {
        "kind": "unsupported",
        "status": "reading_file",
        "label": original_name,
        "content": f"[UPLOAD NOTICE]\nFile {original_name} uploaded, but this file type is not supported yet."
    }


def read_urls_context(user_message: str, max_urls: int = 3) -> List[Dict]:
    urls = extract_urls(user_message)
    contexts = []

    for url in urls[:max_urls]:
        try:
            contexts.append({
                "kind": "url",
                "status": "reading_url",
                "label": url,
                "content": f"[URL READ: {url}]\n{read_url(url)}"
            })
        except Exception as e:
            contexts.append({
                "kind": "url",
                "status": "reading_url",
                "label": url,
                "content": f"[URL READ ERROR: {url}]\n{e}"
            })

    return contexts


def search_context(query: str, max_results: int = 5) -> Dict:
    try:
        results = search_web(query, max_results=max_results)

        return {
            "kind": "search",
            "status": "searching",
            "label": query,
            "content": "[WEB SEARCH RESULTS]\n" + format_search_results(query, results)
        }

    except Exception as e:
        return {
            "kind": "search",
            "status": "searching",
            "label": query,
            "content": f"[WEB SEARCH ERROR]\n{e}"
        }


def merge_tool_context(contexts: List[Dict], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    parts = []

    for ctx in contexts:
        content = (ctx.get("content") or "").strip()

        if content:
            parts.append(content)

    return safe_truncate("\n\n".join(parts), max_chars)
