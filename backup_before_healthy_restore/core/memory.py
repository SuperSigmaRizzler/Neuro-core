import hashlib
from typing import Dict

from config import MEMORY_FILE
from core.utils import load_json, save_json


def make_memory_chat_id(user_id: str, chat_id: str) -> str:
    safe_chat = hashlib.sha256(str(chat_id).encode("utf-8")).hexdigest()[:32]
    return f"{user_id}::{safe_chat}"


def _load() -> Dict:
    return load_json(MEMORY_FILE, {})


def _save(data: Dict) -> None:
    save_json(MEMORY_FILE, data)


def delete_chat_memory(user_id: str, chat_id: str) -> bool:
    memory_id = make_memory_chat_id(user_id, chat_id)
    data = _load()

    existed = memory_id in data

    if existed:
        del data[memory_id]
        _save(data)

    return existed


def delete_all_user_memory(user_id: str) -> int:
    data = _load()
    prefix = f"{user_id}::"

    keys = [key for key in data.keys() if key.startswith(prefix)]

    for key in keys:
        del data[key]

    if keys:
        _save(data)

    return len(keys)
