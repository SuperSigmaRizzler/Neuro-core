from pathlib import Path

p = Path("app.py")
text = p.read_text()

if "import os" not in text.splitlines()[:40]:
    text = "import os\n" + text

needle = '''    def generate():
        full_answer = ""
        thought_seconds = None
        thinking_started_at = None
        used_thinking = False
        first_token_sent = False
'''

insert = '''    def generate():
        full_answer = ""
        thought_seconds = None
        thinking_started_at = None
        used_thinking = False
        first_token_sent = False

        # DRY RUN: test SSE/frontend/backend without calling any AI provider.
        if os.getenv("NEUROMV_DRY_RUN") == "1":
            dry_chat_id = incoming_chat_id or ("guest_chat_" + uuid4().hex)

            yield sse("meta", {
                "chat_id": dry_chat_id,
                "title": "Dry Run Test",
                "selected_mode": selected_mode,
                "runtime_mode": runtime_mode,
                "logged_in": bool(user)
            })

            yield sse("status", {"name": "thinking"})
            yield sse("status", {"name": "clear"})
            yield sse("token", {
                "text": "NeuroMV dry run OK ✅ Backend streaming works without using Groq/Gemini."
            })
            yield sse("done", {
                "ok": True,
                "chat_id": dry_chat_id
            })
            return
'''

if "NEUROMV_DRY_RUN" in text:
    print("✅ Dry run block already exists.")
elif needle in text:
    text = text.replace(needle, insert, 1)
    p.write_text(text)
    print("✅ Dry run block inserted.")
else:
    print("❌ generate() block not found. Kirim: sed -n '640,685p' app.py")
    raise SystemExit
