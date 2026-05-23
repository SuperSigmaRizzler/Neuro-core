import sqlite3
import time
from pathlib import Path

try:
    from config import DATA_DIR
except Exception:
    DATA_DIR = "data"

DB_PATH = Path(DATA_DIR) / "neuromv.db"


def clean(text, limit=260):
    text = str(text or "").replace("\n", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    if len(text) > limit:
        text = text[:limit].rstrip() + "..."
    return text


def table_columns(con, table):
    try:
        rows = con.execute(f"PRAGMA table_info({table})").fetchall()
        return [r[1] for r in rows]
    except Exception:
        return []


def main():
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    msg_cols = table_columns(con, "messages")
    chat_cols = table_columns(con, "chats")

    if not msg_cols:
        print("❌ Table messages not found.")
        return

    if "chat_id" not in msg_cols or "text" not in msg_cols or "role" not in msg_cols:
        print("❌ messages table must have chat_id, role, text columns.")
        print("messages columns:", msg_cols)
        return

    con.execute("""
        CREATE TABLE IF NOT EXISTS brain_chat_summaries (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)

    # Try to map chat_id -> user_id from chats table if possible.
    chat_user = {}

    if chat_cols and "id" in chat_cols and "user_id" in chat_cols:
        for r in con.execute("SELECT id, user_id FROM chats"):
            cid = str(r["id"])
            uid = str(r["user_id"] or "guest")
            chat_user[cid] = uid

    # If messages has user_id, use it as fallback.
    msg_has_user_id = "user_id" in msg_cols

    chat_ids = [
        str(r["chat_id"])
        for r in con.execute("SELECT DISTINCT chat_id FROM messages WHERE chat_id IS NOT NULL")
    ]

    now = int(time.time())
    count = 0

    for cid in chat_ids:
        rows = con.execute("""
            SELECT *
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            LIMIT 80
        """, (cid,)).fetchall()

        if not rows:
            continue

        user_id = chat_user.get(cid)

        if not user_id and msg_has_user_id:
            for r in rows:
                if r["user_id"]:
                    user_id = str(r["user_id"])
                    break

        if not user_id:
            user_id = "guest"

        parts = []
        for r in rows[-30:]:
            role = clean(r["role"], 20)
            text = clean(r["text"], 280)
            if not text:
                continue
            parts.append(f"{role}: {text}")

        if not parts:
            continue

        summary = "Backfilled previous chat context:\n" + "\n".join(parts)

        # Store using raw user_id.
        con.execute("""
            INSERT INTO brain_chat_summaries(chat_id, user_id, summary, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id)
            DO UPDATE SET summary = excluded.summary, user_id = excluded.user_id, updated_at = excluded.updated_at
        """, (cid, user_id, summary, now, now))

        # Also store a duplicate key form if your app uses user_key like user:<id>.
        # Since chat_id is primary key, we cannot duplicate same chat_id.
        # So we keep primary owner as user_id here.
        count += 1

    con.commit()
    con.close()

    print(f"✅ Backfilled {count} chat summaries into brain memory.")


if __name__ == "__main__":
    main()
