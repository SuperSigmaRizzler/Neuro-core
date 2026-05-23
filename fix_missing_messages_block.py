from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

anchor = 'lesson_context = "\\n\\n---\\n\\n".join(context_blocks)'

messages_block = '''
            messages = build_messages_from_history(
                history=history,
                user_message=user_message or f"Analyze uploaded file: {(upload_row or {}).get('original_name', 'file')}",
                mode=runtime_mode,
                tool_context=tool_context,
                lesson_context=lesson_context
            )
'''

if "messages = build_messages_from_history(" in text:
    print("✅ messages block already exists.")
elif anchor in text:
    text = text.replace(anchor, anchor + "\n" + messages_block, 1)
    p.write_text(text, encoding="utf-8")
    print("✅ Restored messages = build_messages_from_history(...) block.")
else:
    print("⚠️ Anchor not found. Show lines 850-885 with:")
    print("sed -n '850,885p' app.py")
