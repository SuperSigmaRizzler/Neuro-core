from pathlib import Path

p = Path("app.py")
text = p.read_text()

# 1) Remove all previous broken DEBUG_CHAT lines
lines = []
removed = 0

for line in text.splitlines():
    if "DEBUG_CHAT:" in line:
        removed += 1
        continue
    lines.append(line)

text = "\n".join(lines) + "\n"

# 2) Add safe debug checkpoints only in safe places
def add_before(needle, insert):
    global text
    if insert.strip() in text:
        return
    if needle not in text:
        print("❌ needle not found:", needle[:90])
        return
    text = text.replace(needle, insert + needle, 1)

def add_after(needle, insert):
    global text
    if insert.strip() in text:
        return
    if needle not in text:
        print("❌ needle not found:", needle[:90])
        return
    text = text.replace(needle, needle + insert, 1)

add_after(
'''def chat():
    data, upload = get_request_data()
''',
'''    print("DEBUG_CHAT: after get_request_data", flush=True)
'''
)

add_after(
'''    intent_info = classify_user_intent(
        user_message or ((upload.filename or "") if upload else "")
    )
''',
'''    print("DEBUG_CHAT: after classify_user_intent", flush=True)
'''
)

add_after(
'''    runtime_mode = choose_runtime_mode(selected_mode, user_message, intent_info)
''',
'''    print("DEBUG_CHAT: after choose_runtime_mode", flush=True)
'''
)

add_after(
'''    def generate():
''',
'''        print("DEBUG_CHAT: generator started", flush=True)
'''
)

# IMPORTANT: before yield sse("meta", { ... }), not after it.
add_before(
'''            yield sse("meta", {
''',
'''            print("DEBUG_CHAT: before meta yield", flush=True)
'''
)

# IMPORTANT: before the for-loop, not inside it.
add_before(
'''            for token in stream_model_response(messages, runtime_mode):
''',
'''            print("DEBUG_CHAT: before stream_model_response loop", flush=True)
'''
)

p.write_text(text)

print(f"✅ removed {removed} old DEBUG_CHAT lines")
print("✅ safe debug checkpoints installed")
