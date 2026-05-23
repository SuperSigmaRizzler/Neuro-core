from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = '''            brain_context = ""

            if user:
                db_add_message('''

new = '''            brain_context = ""

            context_blocks = [INTERNAL_SECURITY_CONTEXT]

            if brain_context:
                context_blocks.append(brain_context)

            if lesson_context:
                context_blocks.append(lesson_context)

            lesson_context = "\\n\\n---\\n\\n".join(context_blocks)

            messages = build_messages_from_history(
                history=history,
                user_message=user_message or f"Analyze uploaded file: {(upload_row or {}).get('original_name', 'file')}",
                mode=runtime_mode,
                tool_context=tool_context,
                lesson_context=lesson_context
            )

            if user:
                db_add_message('''

if old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("✅ Restored context_blocks + messages block.")
elif "messages = build_messages_from_history(" in text:
    print("✅ messages block already exists.")
else:
    print("⚠️ Could not patch automatically. Show lines 855-875:")
    print("sed -n '855,875p' app.py")
