from pathlib import Path

p = Path("app.py")
text = p.read_text()

def add_before(needle, insert):
    global text
    if insert.strip() in text:
        return
    if needle not in text:
        print("❌ needle not found:", needle[:90])
        return
    text = text.replace(needle, insert + needle, 1)

add_before(
'''            tool_context = merge_tool_context(contexts)
''',
'''            print("DEBUG_CHAT: before merge_tool_context", flush=True)
'''
)

add_before(
'''            lesson_context = lessons_prompt_context(
''',
'''            print("DEBUG_CHAT: before lessons_prompt_context", flush=True)
'''
)

add_before(
'''            username_for_memory = ""
''',
'''            print("DEBUG_CHAT: after lessons_prompt_context", flush=True)
'''
)

add_before(
'''            messages = build_messages_from_history(
''',
'''            print("DEBUG_CHAT: before build_messages_from_history", flush=True)
'''
)

add_before(
'''            if user:
                db_add_message(
''',
'''            print("DEBUG_CHAT: before db_add_message user message", flush=True)
'''
)

add_before(
'''            # -----------------------------
            # Stream model response.
''',
'''            print("DEBUG_CHAT: reached stream section", flush=True)
'''
)

p.write_text(text)
print("✅ more debug checkpoints added.")
