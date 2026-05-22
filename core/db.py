import os
import re
import sqlite3
import time
import uuid
from typing import Dict, List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from config import DB_FILE
from core.utils import clean_spaces, ensure_parent, now_ts, today_key


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,24}$")


def connect():
    ensure_parent(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            thought_seconds INTEGER,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(chat_id) REFERENCES chats(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id TEXT PRIMARY KEY,
            user_key TEXT NOT NULL,
            user_id TEXT,
            chat_id TEXT,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            path TEXT NOT NULL,
            mime_type TEXT,
            extension TEXT,
            size_bytes INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS usage_limits (
            id TEXT PRIMARY KEY,
            user_key TEXT NOT NULL,
            kind TEXT NOT NULL,
            day TEXT NOT NULL,
            count INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            UNIQUE(user_key, kind, day)
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS chat_tool_notes (
            id TEXT PRIMARY KEY,
            user_key TEXT NOT NULL,
            chat_id TEXT,
            tool_type TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS assistant_lessons (
            id TEXT PRIMARY KEY,
            user_key TEXT NOT NULL,
            chat_id TEXT,
            lesson TEXT NOT NULL,
            source_text TEXT,
            importance INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)


        db.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_updated ON chats(user_id, updated_at DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_time ON messages(chat_id, created_at ASC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_day ON usage_limits(user_key, day)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_uploads_user_chat ON uploaded_files(user_key, chat_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tool_notes_chat ON chat_tool_notes(user_key, chat_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_lessons_user_time ON assistant_lessons(user_key, updated_at DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_lessons_chat ON assistant_lessons(user_key, chat_id)")


# =========================
# USERS / NEUROACC
# =========================

def validate_username(username: str) -> Optional[str]:
    if not USERNAME_RE.match(username or ""):
        return "Username harus 3-24 karakter, hanya huruf, angka, dan underscore."
    return None


def validate_password(password: str) -> Optional[str]:
    if len(password or "") < 6:
        return "Password minimal 6 karakter."
    if len(password or "") > 128:
        return "Password terlalu panjang."
    return None


def public_user(row) -> Dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["username"],
        "email": f'{row["username"]}@neuroacc.local',
        "picture": ""
    }


def create_user(username: str, password: str) -> Dict:
    username = (username or "").strip()

    err = validate_username(username) or validate_password(password)
    if err:
        raise ValueError(err)

    user_id = "acc_" + uuid.uuid4().hex
    password_hash = generate_password_hash(password)

    try:
        with connect() as db:
            db.execute(
                "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username, password_hash, now_ts())
            )

            row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return public_user(row)

    except sqlite3.IntegrityError:
        raise ValueError("Username sudah dipakai.")


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    username = (username or "").strip()

    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not row:
        return None

    if not check_password_hash(row["password_hash"], password or ""):
        return None

    return public_user(row)


# =========================
# CHATS
# =========================

def make_title(text: str) -> str:
    clean = clean_spaces(text)
    if not clean:
        return "New Chat"
    return clean[:34] + ("..." if len(clean) > 34 else "")


def get_chats(user_id: str) -> List[Dict]:
    with connect() as db:
        rows = db.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chats
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,)
        ).fetchall()

    return [dict(row) for row in rows]


def get_chat(user_id: str, chat_id: str) -> Optional[Dict]:
    with connect() as db:
        row = db.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chats
            WHERE id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        ).fetchone()

    return dict(row) if row else None


def user_exists(user_id) -> bool:
    if user_id is None:
        return False

    try:
        with get_db() as db:
            row = db.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

        return row is not None

    except Exception:
        return False


def safe_user_id(user_id):
    """
    Railway/browser sessions can outlive the SQLite user row.
    If session contains a stale user_id, do not let chat creation crash.
    """
    if user_id is None:
        return None

    if user_exists(user_id):
        return user_id

    return None


def create_chat(user_id: str, first_message: str = "") -> Dict:

    user_id = safe_user_id(user_id)
    chat_id = "chat_" + uuid.uuid4().hex
    title = make_title(first_message)
    t = now_ts()

    with connect() as db:
        db.execute(
            """
            INSERT INTO chats (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, user_id, title, t, t)
        )

    return {
        "id": chat_id,
        "title": title,
        "created_at": t,
        "updated_at": t
    }


def ensure_chat(user_id: str, chat_id: Optional[str], first_message: str = "") -> Dict:
    user_id = safe_user_id(user_id)
    if chat_id:
        chat = get_chat(user_id, chat_id)
        if chat:
            return chat

    return create_chat(user_id, first_message)


def update_chat_title(user_id: str, chat_id: str, title: str) -> bool:
    title = clean_spaces(title)[:60] or "New Chat"

    with connect() as db:
        cur = db.execute(
            """
            UPDATE chats
            SET title = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, now_ts(), chat_id, user_id)
        )

    return cur.rowcount > 0


def delete_chat(user_id: str, chat_id: str) -> Dict:
    deleted_upload_paths = []

    with connect() as db:
        chat = db.execute(
            "SELECT id FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, user_id)
        ).fetchone()

        if not chat:
            return {
                "deleted": False,
                "upload_paths": []
            }

        upload_rows = db.execute(
            "SELECT path FROM uploaded_files WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        ).fetchall()

        deleted_upload_paths = [row["path"] for row in upload_rows]

        db.execute("DELETE FROM messages WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        db.execute("DELETE FROM uploaded_files WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        db.execute("DELETE FROM chat_tool_notes WHERE chat_id = ? AND user_key = ?", (chat_id, f"user:{user_id}"))
        db.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))

    return {
        "deleted": True,
        "upload_paths": deleted_upload_paths
    }


# =========================
# MESSAGES
# =========================

def add_message(
    user_id: str,
    chat_id: str,
    role: str,
    text: str,
    thought_seconds: Optional[int] = None
) -> Dict:
    msg_id = "msg_" + uuid.uuid4().hex
    t = now_ts()

    with connect() as db:
        db.execute(
            """
            INSERT INTO messages (id, chat_id, user_id, role, text, thought_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (msg_id, chat_id, user_id, role, text, thought_seconds, t)
        )

        db.execute(
            "UPDATE chats SET updated_at = ? WHERE id = ? AND user_id = ?",
            (t, chat_id, user_id)
        )

    return {
        "id": msg_id,
        "role": role,
        "text": text,
        "thoughtSeconds": thought_seconds,
        "time": t
    }


def get_messages(user_id: str, chat_id: str, limit: int = 200) -> List[Dict]:
    with connect() as db:
        rows = db.execute(
            """
            SELECT id, role, text, thought_seconds, created_at
            FROM messages
            WHERE chat_id = ? AND user_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (chat_id, user_id, limit)
        ).fetchall()

    return [
        {
            "id": row["id"],
            "role": row["role"],
            "text": row["text"],
            "thoughtSeconds": row["thought_seconds"],
            "time": row["created_at"]
        }
        for row in rows
    ]


def get_recent_model_history(user_id: str, chat_id: str, limit: int = 20) -> List[Dict[str, str]]:
    messages = get_messages(user_id, chat_id, limit=limit)

    return [
        {
            "role": msg["role"],
            "content": msg["text"]
        }
        for msg in messages[-limit:]
        if msg["role"] in ["user", "assistant"]
    ]


# =========================
# UPLOADS
# =========================

def record_upload(
    *,
    user_key: str,
    original_name: str,
    stored_name: str,
    path: str,
    size_bytes: int,
    user_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    mime_type: Optional[str] = None,
    extension: Optional[str] = None
) -> Dict:
    upload_id = "up_" + uuid.uuid4().hex
    t = now_ts()

    with connect() as db:
        db.execute(
            """
            INSERT INTO uploaded_files (
                id, user_key, user_id, chat_id, original_name, stored_name,
                path, mime_type, extension, size_bytes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                upload_id,
                user_key,
                user_id,
                chat_id,
                original_name,
                stored_name,
                path,
                mime_type,
                extension,
                size_bytes,
                t
            )
        )

    return {
        "id": upload_id,
        "user_key": user_key,
        "user_id": user_id,
        "chat_id": chat_id,
        "original_name": original_name,
        "stored_name": stored_name,
        "path": path,
        "mime_type": mime_type,
        "extension": extension,
        "size_bytes": size_bytes,
        "created_at": t
    }


def attach_upload_to_chat(upload_id: str, chat_id: str, user_id: Optional[str] = None) -> bool:
    with connect() as db:
        if user_id:
            cur = db.execute(
                """
                UPDATE uploaded_files
                SET chat_id = ?, user_id = ?
                WHERE id = ?
                """,
                (chat_id, user_id, upload_id)
            )
        else:
            cur = db.execute(
                """
                UPDATE uploaded_files
                SET chat_id = ?
                WHERE id = ?
                """,
                (chat_id, upload_id)
            )

    return cur.rowcount > 0


def get_uploads_for_chat(user_key: str, chat_id: str) -> List[Dict]:
    with connect() as db:
        rows = db.execute(
            """
            SELECT *
            FROM uploaded_files
            WHERE user_key = ? AND chat_id = ?
            ORDER BY created_at ASC
            """,
            (user_key, chat_id)
        ).fetchall()

    return [dict(row) for row in rows]


def remove_upload_files(paths: List[str]) -> int:
    removed = 0

    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                removed += 1
        except Exception:
            continue

    return removed


# =========================
# LIMITS
# =========================

def get_usage(user_key: str, kind: str) -> int:
    day = today_key()

    with connect() as db:
        row = db.execute(
            """
            SELECT count
            FROM usage_limits
            WHERE user_key = ? AND kind = ? AND day = ?
            """,
            (user_key, kind, day)
        ).fetchone()

    return int(row["count"]) if row else 0


def check_and_increment_usage(user_key: str, kind: str, limit: int) -> Dict:
    day = today_key()
    t = now_ts()
    row_id = f"{user_key}:{kind}:{day}"

    with connect() as db:
        row = db.execute(
            """
            SELECT count
            FROM usage_limits
            WHERE user_key = ? AND kind = ? AND day = ?
            """,
            (user_key, kind, day)
        ).fetchone()

        current = int(row["count"]) if row else 0

        if current >= limit:
            return {
                "ok": False,
                "count": current,
                "limit": limit,
                "kind": kind,
                "day": day
            }

        if row:
            db.execute(
                """
                UPDATE usage_limits
                SET count = count + 1, updated_at = ?
                WHERE user_key = ? AND kind = ? AND day = ?
                """,
                (t, user_key, kind, day)
            )
        else:
            db.execute(
                """
                INSERT INTO usage_limits (id, user_key, kind, day, count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (row_id, user_key, kind, day, 1, t)
            )

    return {
        "ok": True,
        "count": current + 1,
        "limit": limit,
        "kind": kind,
        "day": day
    }


# =========================
# TOOL NOTES
# =========================

def add_tool_note(user_key: str, tool_type: str, note: str, chat_id: Optional[str] = None) -> Dict:
    note_id = "tool_" + uuid.uuid4().hex
    t = now_ts()

    with connect() as db:
        db.execute(
            """
            INSERT INTO chat_tool_notes (id, user_key, chat_id, tool_type, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (note_id, user_key, chat_id, tool_type, note, t)
        )

    return {
        "id": note_id,
        "user_key": user_key,
        "chat_id": chat_id,
        "tool_type": tool_type,
        "note": note,
        "created_at": t
    }


def get_recent_tool_notes(user_key: str, chat_id: Optional[str] = None, limit: int = 12) -> List[Dict]:
    with connect() as db:
        if chat_id:
            rows = db.execute(
                """
                SELECT *
                FROM chat_tool_notes
                WHERE user_key = ? AND chat_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_key, chat_id, limit)
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT *
                FROM chat_tool_notes
                WHERE user_key = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_key, limit)
            ).fetchall()

    return [dict(row) for row in rows]


# =========================
# AUTO LESSONS / LEARN FROM MISTAKES
# =========================

def add_assistant_lesson(
    user_key: str,
    lesson: str,
    source_text: str = "",
    chat_id: Optional[str] = None,
    importance: int = 1
) -> Dict:
    lesson = clean_spaces(lesson)[:800]
    source_text = str(source_text or "")[:1600]
    importance = max(1, min(int(importance or 1), 5))

    if not lesson:
        raise ValueError("Lesson kosong.")

    lesson_id = "lesson_" + uuid.uuid4().hex
    t = now_ts()

    with connect() as db:
        db.execute(
            """
            INSERT INTO assistant_lessons (
                id, user_key, chat_id, lesson, source_text,
                importance, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lesson_id,
                user_key,
                chat_id,
                lesson,
                source_text,
                importance,
                t,
                t
            )
        )

    return {
        "id": lesson_id,
        "user_key": user_key,
        "chat_id": chat_id,
        "lesson": lesson,
        "source_text": source_text,
        "importance": importance,
        "created_at": t,
        "updated_at": t
    }


def get_assistant_lessons(
    user_key: str,
    chat_id: Optional[str] = None,
    limit: int = 12
) -> List[Dict]:
    with connect() as db:
        if chat_id:
            rows = db.execute(
                """
                SELECT *
                FROM assistant_lessons
                WHERE user_key = ? AND (chat_id = ? OR chat_id IS NULL)
                ORDER BY importance DESC, updated_at DESC
                LIMIT ?
                """,
                (user_key, chat_id, limit)
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT *
                FROM assistant_lessons
                WHERE user_key = ?
                ORDER BY importance DESC, updated_at DESC
                LIMIT ?
                """,
                (user_key, limit)
            ).fetchall()

    return [dict(row) for row in rows]


def delete_assistant_lesson(user_key: str, lesson_id: str) -> bool:
    with connect() as db:
        cur = db.execute(
            "DELETE FROM assistant_lessons WHERE id = ? AND user_key = ?",
            (lesson_id, user_key)
        )

    return cur.rowcount > 0


def delete_all_assistant_lessons(user_key: str) -> int:
    with connect() as db:
        cur = db.execute(
            "DELETE FROM assistant_lessons WHERE user_key = ?",
            (user_key,)
        )

    return cur.rowcount


def format_lessons_for_prompt(lessons: List[Dict]) -> str:
    if not lessons:
        return ""

    lines = []

    for i, lesson in enumerate(lessons, start=1):
        text = clean_spaces(lesson.get("lesson", ""))
        if text:
            lines.append(f"{i}. {text}")

    if not lines:
        return ""

    return "User/project lessons learned from previous corrections:\n" + "\n".join(lines)
