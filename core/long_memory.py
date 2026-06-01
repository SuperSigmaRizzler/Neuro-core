import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    from config import DATA_DIR
except Exception:
    DATA_DIR = "data"

try:
    from core.utils import clean_spaces
except Exception:
    def clean_spaces(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()


DB_PATH = Path(DATA_DIR) / "neuromv.db"


# ==================================================
# Safety
# ==================================================

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{12,}",
    r"gsk_[A-Za-z0-9_-]{12,}",
    r"AIza[A-Za-z0-9_-]{20,}",
    r"api[_ -]?key\s*[:=]",
    r"password\s*[:=]",
    r"passwd\s*[:=]",
    r"secret\s*[:=]",
    r"token\s*[:=]",
    r"bearer\s+[A-Za-z0-9._-]+",
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
]


def _now() -> int:
    return int(time.time())


def _connect():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _safe_text(text: str, limit: int = 4000) -> str:
    text = clean_spaces(text)
    if len(text) > limit:
        text = text[:limit].rstrip() + "..."
    return text


def _contains_secret(text: str) -> bool:
    return any(re.search(pattern, text or "", re.IGNORECASE) for pattern in SECRET_PATTERNS)


def _json_from_text(text: str) -> Dict:
    text = (text or "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _as_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    raw = str(value).strip().lower()

    if raw in {"true", "yes", "1", "on"}:
        return True

    if raw in {"false", "no", "0", "off"}:
        return False

    return default


def _as_int(value, default=1, min_value=1, max_value=5) -> int:
    try:
        n = int(value)
    except Exception:
        n = default

    return max(min_value, min(max_value, n))


# ==================================================
# Tables
# ==================================================

def init_long_memory_tables() -> None:
    with _connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS long_memory_items (
                id TEXT PRIMARY KEY,
                user_key TEXT NOT NULL,
                chat_id TEXT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 3,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS long_memory_chat_state (
                user_key TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                detailed_timeline TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY(user_key, chat_id)
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS long_memory_profile (
                user_key TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                importance INTEGER DEFAULT 3,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY(user_key, key)
            )
        """)

        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_long_memory_user_time
            ON long_memory_items(user_key, updated_at DESC)
        """)

        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_long_memory_user_kind
            ON long_memory_items(user_key, kind, updated_at DESC)
        """)


# ==================================================
# Semantic extraction
# ==================================================

def extract_memory_semantically(
    *,
    user_message: str,
    assistant_message: str = "",
    recent_context: str = ""
) -> Dict:
    """
    Uses the model to decide what should become cross-chat memory.
    Not keyword-based. If uncertain/fails, learn nothing.
    """
    user_message = _safe_text(user_message, 3000)
    assistant_message = _safe_text(assistant_message, 3000)
    recent_context = _safe_text(recent_context, 3000)

    empty = {
        "should_store": False,
        "items": [],
        "profile": {},
        "chat_summary_update": ""
    }

    combined = "\n".join([user_message, assistant_message, recent_context])

    if not combined.strip():
        return empty

    if _contains_secret(combined):
        return empty

    try:
        from providers.router import complete_model_response

        messages = [
            {
                "role": "system",
                "content": (
                    "You are NeuroMV's private long-term memory extractor. "
                    "Return valid JSON only. Do not answer the user.\n\n"

                    "Goal: build a cross-chat memory like a quiet background chronicle. "
                    "Store durable context that helps future conversations feel continuous.\n\n"

                    "Store when useful:\n"
                    "- long-term user preferences;\n"
                    "- project facts and current project state;\n"
                    "- important debugging history and decisions;\n"
                    "- repeated corrections about how NeuroMV should behave;\n"
                    "- stable workflow preferences;\n"
                    "- important milestones or outcomes;\n"
                    "- learning sessions and topics the user studied, especially if the user may later ask what was discussed;\n"
                    "- useful conversation summaries such as 'the user learned Python basics' or 'the user debugged streaming'.\n\n"

                    "Do NOT store:\n"
                    "- ordinary one-off questions that have no future continuity value;\n"
                    "- jokes with no future use;\n"
                    "- temporary logs/errors unless they are part of project history;\n"
                    "- passwords, API keys, tokens, secrets, .env values, credentials;\n"
                    "- private details that are not useful for future assistance.\n\n"

                    "Important memory behavior:\n"
                    "- If the user asks to learn something, store a concise memory of the learning topic and level.\n"
                    "- If the user later asks 'kemarin kita bahas apa?', memory should help answer that.\n"
                    "- Do not wait for explicit words like 'remember this' when the session topic is useful for continuity.\n\n"

                    "Memory should be detailed enough to preserve context, but concise. "
                    "Write items as facts/instructions for future NeuroMV behavior.\n\n"

                    "Use these item kinds when relevant:\n"
                    "- preference\n"
                    "- project_state\n"
                    "- correction\n"
                    "- milestone\n"
                    "- workflow\n"
                    "- caution\n"
                    "- context\n"
                    "- learning_session\n\n"

                    "Learning-session memory behavior:\n"
                    "- If the user asks to learn something, store a concise memory of the learning topic and level when useful for continuity.\n"
                    "- If the user later asks what was discussed yesterday/earlier, memory should help answer.\n"
                    "- Teaching Python/basic coding from general knowledge should not require web search.\n"
                    "- Do not wait for explicit 'remember this' if the session topic is useful for future continuity.\n\n"
                    "Return exactly this JSON shape:\n"
                    "{\n"
                    '  "should_store": true/false,\n'
                    '  "items": [\n'
                    "    {\n"
                    '      "kind": "preference|project_state|correction|milestone|workflow|caution|context",\n'
                    '      "title": "short title",\n'
                    '      "content": "memory item content",\n'
                    '      "importance": 1-5\n'
                    "    }\n"
                    "  ],\n"
                    '  "profile": {\n'
                    '    "optional_stable_key": "optional stable value"\n'
                    "  },\n"
                    '  "chat_summary_update": "short summary of what happened in this turn, or empty string"\n'
                    "}"
                )
            },
            {
                "role": "user",
                "content": (
                    "Recent context:\n"
                    f"{recent_context}\n\n"
                    "User message:\n"
                    f"{user_message}\n\n"
                    "Assistant message:\n"
                    f"{assistant_message}"
                )
            }
        ]

        raw = complete_model_response(messages, "instant")
        data = _json_from_text(raw)

        if not isinstance(data, dict):
            return empty

        should_store = _as_bool(data.get("should_store"), False)
        items = data.get("items", [])
        profile = data.get("profile", {})
        chat_summary_update = _safe_text(data.get("chat_summary_update", ""), 1200)

        if not should_store:
            return empty

        if not isinstance(items, list):
            items = []

        if not isinstance(profile, dict):
            profile = {}

        clean_items = []

        for item in items[:8]:
            if not isinstance(item, dict):
                continue

            kind = _safe_text(item.get("kind", "context"), 40).lower()
            title = _safe_text(item.get("title", ""), 90)
            content = _safe_text(item.get("content", ""), 1500)
            importance = _as_int(item.get("importance", 3), default=3)

            if not title or not content:
                continue

            if _contains_secret(title) or _contains_secret(content):
                continue

            if kind not in {
                "preference",
                "project_state",
                "correction",
                "milestone",
                "workflow",
                "caution",
                "context",
                "learning_session",
            }:
                kind = "context"

            clean_items.append({
                "kind": kind,
                "title": title,
                "content": content,
                "importance": importance
            })

        clean_profile = {}

        for key, value in list(profile.items())[:12]:
            key = _safe_text(key, 60).lower().replace(" ", "_")
            value = _safe_text(value, 700)

            if not key or not value:
                continue

            if _contains_secret(key) or _contains_secret(value):
                continue

            clean_profile[key] = value

        if not clean_items and not clean_profile and not chat_summary_update:
            return empty

        return {
            "should_store": True,
            "items": clean_items,
            "profile": clean_profile,
            "chat_summary_update": chat_summary_update
        }

    except Exception:
        return empty


# ==================================================
# Write memory
# ==================================================

def store_memory_item(
    *,
    user_key: str,
    chat_id: Optional[str],
    kind: str,
    title: str,
    content: str,
    importance: int = 3
) -> bool:
    init_long_memory_tables()

    user_key = _safe_text(user_key, 120)
    chat_id = _safe_text(chat_id or "", 160) or None
    kind = _safe_text(kind or "context", 40).lower()
    title = _safe_text(title, 90)
    content = _safe_text(content, 1500)
    importance = _as_int(importance, 3)

    if not user_key or not title or not content:
        return False

    if _contains_secret(title) or _contains_secret(content):
        return False

    now = _now()

    # Simple stable-ish id to avoid endless duplicates.
    raw_id = f"{user_key}|{kind}|{title.lower()}|{content[:160].lower()}"
    import hashlib
    mem_id = "lm_" + hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:32]

    with _connect() as con:
        existing = con.execute(
            "SELECT id, importance FROM long_memory_items WHERE id = ?",
            (mem_id,)
        ).fetchone()

        if existing:
            con.execute("""
                UPDATE long_memory_items
                SET importance = ?, updated_at = ?
                WHERE id = ?
            """, (max(int(existing["importance"] or 1), importance), now, mem_id))
        else:
            con.execute("""
                INSERT INTO long_memory_items(
                    id, user_key, chat_id, kind, title, content,
                    importance, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mem_id, user_key, chat_id, kind, title, content,
                importance, now, now
            ))

    return True


def set_profile_memory(
    *,
    user_key: str,
    key: str,
    value: str,
    importance: int = 3
) -> bool:
    init_long_memory_tables()

    user_key = _safe_text(user_key, 120)
    key = _safe_text(key, 60).lower().replace(" ", "_")
    value = _safe_text(value, 700)
    importance = _as_int(importance, 3)

    if not user_key or not key or not value:
        return False

    if _contains_secret(key) or _contains_secret(value):
        return False

    now = _now()

    with _connect() as con:
        con.execute("""
            INSERT INTO long_memory_profile(user_key, key, value, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_key, key) DO UPDATE SET
                value = excluded.value,
                importance = max(long_memory_profile.importance, excluded.importance),
                updated_at = excluded.updated_at
        """, (user_key, key, value, importance, now, now))

    return True


def update_chat_state(
    *,
    user_key: str,
    chat_id: str,
    summary_update: str,
    max_timeline_chars: int = 12000
) -> bool:
    init_long_memory_tables()

    user_key = _safe_text(user_key, 120)
    chat_id = _safe_text(chat_id, 160)
    summary_update = _safe_text(summary_update, 1200)

    if not user_key or not chat_id or not summary_update:
        return False

    if _contains_secret(summary_update):
        return False

    now = _now()

    with _connect() as con:
        row = con.execute("""
            SELECT summary, detailed_timeline
            FROM long_memory_chat_state
            WHERE user_key = ? AND chat_id = ?
        """, (user_key, chat_id)).fetchone()

        if row:
            old_summary = row["summary"] or ""
            old_timeline = row["detailed_timeline"] or ""

            new_summary = _safe_text(
                old_summary + " " + summary_update,
                2200
            )

            new_timeline = (old_timeline + "\n- " + summary_update).strip()

            if len(new_timeline) > max_timeline_chars:
                new_timeline = new_timeline[-max_timeline_chars:].lstrip()

            con.execute("""
                UPDATE long_memory_chat_state
                SET summary = ?, detailed_timeline = ?, updated_at = ?
                WHERE user_key = ? AND chat_id = ?
            """, (new_summary, new_timeline, now, user_key, chat_id))
        else:
            con.execute("""
                INSERT INTO long_memory_chat_state(
                    user_key, chat_id, summary, detailed_timeline, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_key,
                chat_id,
                summary_update,
                "- " + summary_update,
                now,
                now
            ))

    return True


def maybe_update_long_memory(
    *,
    user_key: str,
    chat_id: Optional[str],
    user_message: str,
    assistant_message: str = "",
    recent_context: str = ""
) -> Dict:
    init_long_memory_tables()

    user_key = _safe_text(user_key, 120)
    chat_id = _safe_text(chat_id or "", 160) or None

    result = extract_memory_semantically(
        user_message=user_message,
        assistant_message=assistant_message,
        recent_context=recent_context
    )

    if not result.get("should_store"):
        return {
            "stored_items": 0,
            "stored_profile": 0,
            "updated_chat_state": False
        }

    stored_items = 0
    stored_profile = 0
    updated_chat_state = False

    for item in result.get("items", []):
        ok = store_memory_item(
            user_key=user_key,
            chat_id=chat_id,
            kind=item.get("kind", "context"),
            title=item.get("title", ""),
            content=item.get("content", ""),
            importance=item.get("importance", 3)
        )
        if ok:
            stored_items += 1

    for key, value in (result.get("profile") or {}).items():
        ok = set_profile_memory(
            user_key=user_key,
            key=key,
            value=value,
            importance=3
        )
        if ok:
            stored_profile += 1

    if chat_id and result.get("chat_summary_update"):
        updated_chat_state = update_chat_state(
            user_key=user_key,
            chat_id=chat_id,
            summary_update=result.get("chat_summary_update", "")
        )

    return {
        "stored_items": stored_items,
        "stored_profile": stored_profile,
        "updated_chat_state": updated_chat_state
    }


# ==================================================
# Retrieve memory
# ==================================================

def _token_score(query: str, text: str) -> int:
    # Retrieval scoring only. Not intent routing.
    # This is acceptable as a cheap local DB ranking fallback.
    q = set(re.findall(r"[A-Za-zÀ-ÿ0-9_]{3,}", (query or "").lower()))
    t = set(re.findall(r"[A-Za-zÀ-ÿ0-9_]{3,}", (text or "").lower()))

    if not q or not t:
        return 0

    return len(q & t)


def retrieve_long_memory(
    *,
    user_key: str,
    chat_id: Optional[str],
    user_message: str,
    limit: int = 18
) -> str:
    init_long_memory_tables()

    user_key = _safe_text(user_key, 120)
    chat_id = _safe_text(chat_id or "", 160) or None
    query = _safe_text(user_message, 2000)

    if not user_key:
        return ""

    with _connect() as con:
        profile_rows = con.execute("""
            SELECT key, value, importance
            FROM long_memory_profile
            WHERE user_key = ?
            ORDER BY importance DESC, updated_at DESC
            LIMIT 12
        """, (user_key,)).fetchall()

        item_rows = con.execute("""
            SELECT kind, title, content, importance, updated_at
            FROM long_memory_items
            WHERE user_key = ?
            ORDER BY importance DESC, updated_at DESC
            LIMIT 80
        """, (user_key,)).fetchall()

        chat_row = None
        if chat_id:
            chat_row = con.execute("""
                SELECT summary, detailed_timeline
                FROM long_memory_chat_state
                WHERE user_key = ? AND chat_id = ?
            """, (user_key, chat_id)).fetchone()

    scored = []

    for row in item_rows:
        hay = f"{row['kind']} {row['title']} {row['content']}"
        score = _token_score(query, hay)
        score += int(row["importance"] or 1) * 2

        scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [row for _score, row in scored[:limit]]

    parts = []

    if profile_rows:
        lines = []
        for r in profile_rows:
            lines.append(f"- {r['key']}: {r['value']}")
        parts.append("Global user/project profile:\n" + "\n".join(lines))

    if selected:
        lines = []
        for r in selected:
            lines.append(
                f"- [{r['kind']}; importance {r['importance']}] {r['title']}: {r['content']}"
            )
        parts.append("Cross-chat long memory items:\n" + "\n".join(lines))

    if chat_row:
        parts.append(
            "Current chat memory:\n"
            f"Summary: {chat_row['summary']}\n"
            f"Timeline:\n{chat_row['detailed_timeline']}"
        )

    if not parts:
        return ""

    return "\n\n".join(parts)


def debug_print_long_memory(user_key: str, limit: int = 20) -> None:
    init_long_memory_tables()

    with _connect() as con:
        rows = con.execute("""
            SELECT kind, title, content, importance, chat_id, updated_at
            FROM long_memory_items
            WHERE user_key = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (user_key, limit)).fetchall()

    print(f"Long memory items for {user_key}: {len(rows)}")
    for r in rows:
        print(dict(r))

# ==================================================
# Forced conversation notes
# ==================================================
# This is the "catatan kecil" layer.
# It records actual conversation turns so NeuroMV has cross-chat continuity
# even when semantic memory extraction decides not to store anything.

def record_conversation_note(
    *,
    user_key: str,
    chat_id: str | None,
    user_message: str,
    assistant_message: str,
    importance: int = 4
) -> bool:
    user_message = _safe_text(user_message, 1200)
    assistant_message = _safe_text(assistant_message, 1800)

    if not user_key or not user_message or not assistant_message:
        return False

    combined = user_message + "\n" + assistant_message

    if _contains_secret(combined):
        return False

    title_base = user_message.replace("\n", " ").strip()
    title = "Recent conversation: " + (title_base[:72] + ("..." if len(title_base) > 72 else ""))

    content = (
        "This is an actual previous conversation note.\n"
        f"User: {user_message}\n"
        f"Assistant: {assistant_message}"
    )

    return store_memory_item(
        user_key=user_key,
        chat_id=chat_id,
        kind="conversation_note",
        title=title,
        content=content,
        importance=importance
    )


def retrieve_recent_conversation_notes(
    *,
    user_key: str,
    limit: int = 8
) -> str:
    init_long_memory_tables()

    user_key = _safe_text(user_key, 120)

    if not user_key:
        return ""

    with _connect() as con:
        rows = con.execute("""
            SELECT title, content, chat_id, updated_at
            FROM long_memory_items
            WHERE user_key = ? AND kind = 'conversation_note'
            ORDER BY updated_at DESC
            LIMIT ?
        """, (user_key, limit)).fetchall()

    if not rows:
        return ""

    lines = []

    for r in rows:
        lines.append(
            f"- {r['title']}\n"
            f"  {r['content']}"
        )

    return "Recent cross-chat conversation notes:\n" + "\n".join(lines)
