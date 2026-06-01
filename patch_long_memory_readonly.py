from pathlib import Path

p = Path("app.py")
text = p.read_text()

needle = '''            brain_context = ""
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

insert = '''            long_memory_context = ""
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

if needle not in text:
    print("❌ brain_context block not found.")
    print("Run: sed -n '810,845p' app.py")
    raise SystemExit

text = text.replace(needle, insert, 1)

old_brief = '''                    "- Use memory, project state, learned corrections, and recent chat context first.\\n"
                    "- Do not announce that memory is being used.\\n"
                    "- Search is the final fallback for external/current information.\\n"
'''

new_brief = '''                    "- Use cross-chat long memory, project state, learned corrections, and recent chat context first.\\n"
                    "- Treat memory as background context, not as something to announce.\\n"
                    "- Do not invent memories that are not present in memory/history/context.\\n"
                    "- Search is the final fallback for external/current information.\\n"
'''

if old_brief not in text:
    print("⚠️ briefing text block not found; continuing without changing briefing wording.")
else:
    text = text.replace(old_brief, new_brief, 1)

needle2 = '''            if brain_context:
                memory_blocks.append(
                    "Project / user / chat brain context:\\n" + brain_context
                )

            if learned_lesson_context:
'''

insert2 = '''            if long_memory_context:
                memory_blocks.append(
                    "Cross-chat long-term memory:\\n" + long_memory_context
                )

            if brain_context:
                memory_blocks.append(
                    "Project / user / chat brain context:\\n" + brain_context
                )

            if learned_lesson_context:
'''

if needle2 not in text:
    print("❌ memory_blocks insertion point not found.")
    print("Run: sed -n '835,865p' app.py")
    raise SystemExit

text = text.replace(needle2, insert2, 1)

p.write_text(text)
print("✅ Long memory read-only context injected into app.py")
