from pathlib import Path

p = Path("app.py")
text = p.read_text()

# A) Make long memory read include recent conversation notes.
if "retrieve_recent_conversation_notes" not in text:
    text = text.replace(
        "from core.long_memory import retrieve_long_memory",
        "from core.long_memory import retrieve_long_memory, retrieve_recent_conversation_notes"
    )

    old = '''                long_memory_context = retrieve_long_memory(
                    user_key=user_key,
                    chat_id=real_chat_id,
                    user_message=user_message or "",
                    limit=18
                )
'''

    new = '''                long_memory_context = retrieve_long_memory(
                    user_key=user_key,
                    chat_id=real_chat_id,
                    user_message=user_message or "",
                    limit=18
                )

                recent_long_notes = retrieve_recent_conversation_notes(
                    user_key=user_key,
                    limit=8
                )

                if recent_long_notes:
                    long_memory_context = (
                        (long_memory_context + "\\n\\n") if long_memory_context else ""
                    ) + recent_long_notes
'''

    if old in text:
        text = text.replace(old, new, 1)
        print("✅ recent conversation notes added to long memory read")
    else:
        print("⚠️ long_memory_context read block not found; skipped read enhancement")
else:
    print("ℹ️ recent conversation notes already referenced")

# B) Force-save every completed assistant answer as a conversation note.
if "record_conversation_note(" not in text:
    marker = '''            yield sse("done", {
'''
    idx = text.rfind(marker)

    if idx == -1:
        print("❌ final done marker not found")
        raise SystemExit

    insert = '''            # -----------------------------
            # Forced cross-chat conversation note.
            # This is the small notebook layer: actual previous turns,
            # so New Chat can remember what was discussed.
            # -----------------------------
            if full_answer.strip():
                try:
                    from core.long_memory import record_conversation_note

                    record_conversation_note(
                        user_key=user_key,
                        chat_id=real_chat_id,
                        user_message=user_message or f"[Uploaded file: {(upload_row or {}).get('original_name', 'file')}]",
                        assistant_message=full_answer.strip(),
                        importance=4
                    )
                except Exception:
                    pass

'''
    text = text[:idx] + insert + text[idx:]
    print("✅ forced conversation note auto-save inserted")
else:
    print("ℹ️ forced conversation note already present")

p.write_text(text)
print("✅ patch complete")
