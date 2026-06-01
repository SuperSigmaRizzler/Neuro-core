from pathlib import Path

p = Path("app.py")
text = p.read_text()

old = '''            lesson_context = lessons_prompt_context(
                user_key=user_key,
                chat_id=real_chat_id,
                limit=12
            )

            if lesson_context:
                lesson_context = INTERNAL_SECURITY_CONTEXT + "\\n\\n" + lesson_context
            else:
                lesson_context = INTERNAL_SECURITY_CONTEXT
'''

new = '''            # -----------------------------
            # Brain / memory context.
            # This is NeuroMV's "background briefing":
            # memory first, project state first, tools later.
            # -----------------------------
            learned_lesson_context = lessons_prompt_context(
                user_key=user_key,
                chat_id=real_chat_id,
                limit=12
            )

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

            memory_blocks = [
                INTERNAL_SECURITY_CONTEXT,
                (
                    "NeuroMV Background Briefing:\\n"
                    "- Read this as the assistant's quiet working context before answering.\\n"
                    "- Use memory, project state, learned corrections, and recent chat context first.\\n"
                    "- Do not announce that memory is being used.\\n"
                    "- Search is the final fallback for external/current information.\\n"
                    "- Image generation intent is handled before search.\\n"
                )
            ]

            if brain_context:
                memory_blocks.append(
                    "Project / user / chat brain context:\\n" + brain_context
                )

            if learned_lesson_context:
                memory_blocks.append(
                    "Learned lessons and durable corrections:\\n" + learned_lesson_context
                )

            lesson_context = "\\n\\n".join(block for block in memory_blocks if block)
'''

if old not in text:
    print("❌ target block not found.")
    print("Run this and send output:")
    print("sed -n '805,835p' app.py")
    raise SystemExit

text = text.replace(old, new, 1)
p.write_text(text)
print("✅ app.py now injects NeuroMV brain context into prompt.")
