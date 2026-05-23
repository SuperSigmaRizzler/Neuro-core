from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = """brain_context = build_brain_context(
                user_key=user_key,
                username=username_for_memory
            )"""

new = """brain_context = build_brain_context(
                user_key=user_key,
                chat_id=real_chat_id,
                user_message=user_message,
                username=username_for_memory
            )"""

if old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("✅ Patched build_brain_context call with chat_id + user_message.")
elif "brain_context = build_brain_context(" in text:
    print("⚠️ Found build_brain_context call, but exact format is different.")
    print("Show it with: grep -n -A8 -B4 'brain_context = build_brain_context' app.py")
else:
    print("⚠️ Could not find build_brain_context call.")
