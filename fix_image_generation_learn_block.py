from pathlib import Path

p = Path("app.py")
text = p.read_text()

start_marker = '                answer = make_image_markdown(user_message)'
end_marker = '                yield sse("status", {"name": "clear"})'

start = text.find(start_marker)
if start == -1:
    print("❌ answer = make_image_markdown(user_message) not found")
    raise SystemExit

end = text.find(end_marker, start)
if end == -1:
    print('❌ yield sse("status", {"name": "clear"}) not found after image answer')
    raise SystemExit

replacement = '''                answer = make_image_markdown(user_message)

                if user:
                    db_add_message(user["id"], real_chat_id, "user", user_message)
                    db_add_message(user["id"], real_chat_id, "assistant", answer)

                try:
                    username_for_memory = ""
                    if user and isinstance(user, dict):
                        username_for_memory = str(
                            user.get("username") or user.get("name") or user.get("display_name") or ""
                        )

                    maybe_learn_from_turn(
                        user_message=user_message,
                        assistant_message=answer,
                        user_key=user_key,
                        username=username_for_memory
                    )
                except Exception:
                    pass

'''

text = text[:start] + replacement + text[end:]
p.write_text(text)

print("✅ Fixed broken image generation learn block.")
