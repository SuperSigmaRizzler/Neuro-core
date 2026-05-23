from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = """brain_context = build_brain_context(
                user_key=user_key,
                chat_id=real_chat_id,
                user_message=user_message,
                username=username_for_memory
            )"""

new = """brain_context = """""

if old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("✅ Disabled brain_context call in app.py temporarily.")
else:
    print("⚠️ Exact brain_context block not found.")
    print("Run: grep -n -A8 -B4 'brain_context = build_brain_context' app.py")
