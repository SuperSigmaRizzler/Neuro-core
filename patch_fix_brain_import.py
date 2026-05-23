from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = "from core.brain_context import build_brain_context, maybe_learn_from_turn"
new = "from core.brain_context import build_brain_context, maybe_learn_from_turn, init_brain_tables"

old2 = "from core.brain_context import build_brain_context, maybe_learn_from_turn, refresh_chat_summary_from_db"
new2 = "from core.brain_context import build_brain_context, maybe_learn_from_turn, init_brain_tables, refresh_chat_summary_from_db"

if new2 in text or new in text:
    print("✅ init_brain_tables already imported.")
elif old2 in text:
    text = text.replace(old2, new2, 1)
    p.write_text(text, encoding="utf-8")
    print("✅ Added init_brain_tables to existing brain import.")
elif old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("✅ Added init_brain_tables to brain import.")
else:
    print("⚠️ Could not find brain import line. Show lines 55-70 with: sed -n '55,70p' app.py")
