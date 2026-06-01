from pathlib import Path

p = Path("app.py")
text = p.read_text()

# 1) Ensure import
marker = "from core.prompt_builder import build_messages_from_history\n"
import_line = "from core.public_status import build_public_reasoning_statuses, random_status_delay\n"

if import_line not in text:
    if marker not in text:
        print("❌ prompt_builder import marker not found.")
        raise SystemExit
    text = text.replace(marker, marker + import_line, 1)
    print("✅ public_status import added.")
else:
    print("✅ public_status import already exists.")

# 2) Insert public Pro/Ultra status before streaming
needle = '''            # -----------------------------
            # Stream model response.
            # -----------------------------
            for token in stream_model_response(messages, runtime_mode):
'''

insert = '''            # -----------------------------
            # Public reasoning status for Pro/Ultra.
            # These are high-level visible status lines, not private chain-of-thought.
            # -----------------------------
            if selected_mode in ["pro", "ultra"]:
                if selected_mode == "pro":
                    yield sse("status", {
                        "name": "complex_thinking",
                        "text": "Complex Thinking..."
                    })

                    time.sleep(random_status_delay())

                else:
                    public_statuses = build_public_reasoning_statuses(
                        user_message=user_message or f"Analyze uploaded file: {(upload_row or {}).get('original_name', 'file')}",
                        mode=selected_mode,
                        context_hint="Use safe public high-level reasoning status only."
                    )

                    for line in public_statuses:
                        yield sse("status", {
                            "name": "ultra_public_thinking",
                            "text": line
                        })

                        time.sleep(random_status_delay())

            # -----------------------------
            # Stream model response.
            # -----------------------------
            for token in stream_model_response(messages, runtime_mode):
'''

if "Public reasoning status for Pro/Ultra" not in text:
    if needle not in text:
        print("❌ Stream block needle not found.")
        print("Kirim output: sed -n '885,905p' app.py")
        raise SystemExit
    text = text.replace(needle, insert, 1)
    print("✅ Pro/Ultra public status inserted.")
else:
    print("✅ Pro/Ultra public status already inserted.")

p.write_text(text)
print("Backend public status patch done ✅")
