from pathlib import Path

p = Path("app.py")
text = p.read_text()

# --------------------------------------------------
# A) Ensure read-only long memory is injected.
# If sudah dipasang sebelumnya, skip.
# --------------------------------------------------
if "long_memory_context = retrieve_long_memory(" not in text:
    old = '''            brain_context = ""
            try:
                from core.brain_context import build_brain_context

                brain_context = build_brain_context(
                    user_key,
                    real_chat_id,
                    user_message or ""
                )
            except Exception:
                brain_context = ""
'''

    new = '''            long_memory_context = ""
            try:
                from core.long_memory import retrieve_long_memory

                long_memory_context = retrieve_long_memory(
                    user_key=user_key,
                    chat_id=real_chat_id,
                    user_message=user_message or "",
                    limit=18
                )
            except Exception:
                long_memory_context = ""

            brain_context = ""
            try:
                from core.brain_context import build_brain_context

                brain_context = build_brain_context(
                    user_key,
                    real_chat_id,
                    user_message or ""
                )
            except Exception:
                brain_context = ""
'''

    if old not in text:
        print("❌ read-only insert point not found.")
        print("Run: sed -n '815,850p' app.py")
        raise SystemExit

    text = text.replace(old, new, 1)
    print("✅ read-only long memory inserted.")
else:
    print("ℹ️ read-only long memory already present.")

if "Cross-chat long-term memory:" not in text:
    old = '''            if brain_context:
                memory_blocks.append(
                    "Project / user / chat brain context:\\n" + brain_context
                )

            if learned_lesson_context:
'''

    new = '''            if long_memory_context:
                memory_blocks.append(
                    "Cross-chat long-term memory:\\n" + long_memory_context
                )

            if brain_context:
                memory_blocks.append(
                    "Project / user / chat brain context:\\n" + brain_context
                )

            if learned_lesson_context:
'''

    if old not in text:
        print("❌ memory block insert point not found.")
        print("Run: sed -n '840,870p' app.py")
        raise SystemExit

    text = text.replace(old, new, 1)
    print("✅ long memory block added to prompt.")
else:
    print("ℹ️ long memory prompt block already present.")

# --------------------------------------------------
# B) Auto-save long memory after full assistant answer.
# --------------------------------------------------
if "maybe_update_long_memory(" not in text:
    old = '''            if user and full_answer.strip():
                db_add_message(
                    user["id"],
                    real_chat_id,
                    "assistant",
                    full_answer.strip(),
                    thought_seconds=thought_seconds
                )

            yield sse("done", {
'''

    new = '''            if user and full_answer.strip():
                db_add_message(
                    user["id"],
                    real_chat_id,
                    "assistant",
                    full_answer.strip(),
                    thought_seconds=thought_seconds
                )

            # -----------------------------
            # Long-term memory auto-update.
            # Silent. Never shown in UI.
            # Stores durable project/user context after a complete answer.
            # -----------------------------
            if full_answer.strip():
                try:
                    from core.long_memory import maybe_update_long_memory

                    recent_context_for_memory = ""
                    try:
                        recent_context_for_memory = "\\n".join(
                            f"{m.get('role', 'user')}: {m.get('content') or m.get('text') or ''}"
                            for m in (history or [])[-8:]
                        )
                    except Exception:
                        recent_context_for_memory = ""

                    maybe_update_long_memory(
                        user_key=user_key,
                        chat_id=real_chat_id,
                        user_message=user_message or f"[Uploaded file: {(upload_row or {}).get('original_name', 'file')}]",
                        assistant_message=full_answer.strip(),
                        recent_context=recent_context_for_memory
                    )
                except Exception:
                    pass

            yield sse("done", {
'''

    if old not in text:
        print("❌ stream end insert point not found.")
        print("Run: sed -n '860,890p' app.py")
        raise SystemExit

    text = text.replace(old, new, 1)
    print("✅ auto-save long memory inserted.")
else:
    print("ℹ️ auto-save long memory already present.")

p.write_text(text)
print("✅ Long memory read/write patch complete.")
