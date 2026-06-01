from pathlib import Path

p = Path("core/long_memory.py")
text = p.read_text()

changed = 0

extra_rules = '''                    "Learning-session memory behavior:\\n"
                    "- If the user asks to learn something, store a concise memory of the learning topic and level when useful for continuity.\\n"
                    "- If the user later asks what was discussed yesterday/earlier, memory should help answer.\\n"
                    "- Teaching Python/basic coding from general knowledge should not require web search.\\n"
                    "- Do not wait for explicit 'remember this' if the session topic is useful for future continuity.\\n\\n"
'''

if "Learning-session memory behavior:" not in text:
    marker = '''                    "Return exactly this JSON shape:\\n"'''
    if marker not in text:
        print("❌ marker not found: Return exactly this JSON shape")
        print("Run: grep -n \"Return exactly\\|Store when useful\\|Do NOT store\\|Use these item kinds\" core/long_memory.py")
        raise SystemExit
    text = text.replace(marker, extra_rules + marker, 1)
    changed += 1
    print("✅ inserted learning-session memory rules")
else:
    print("ℹ️ learning-session memory rules already present")

# Add learning_session to prompt kind list if possible
if '"- learning_session' not in text and "- learning_session" not in text:
    marker = '''                    "- context\\n\\n"'''
    if marker in text:
        text = text.replace(marker, '''                    "- context\\n"
                    "- learning_session\\n\\n"''', 1)
        changed += 1
        print("✅ added learning_session to prompt kind list")
    else:
        print("⚠️ prompt kind list marker not found, skipped prompt kind list")

# Add learning_session to allowed validation set
if '''"learning_session"''' not in text:
    marker = '''                "context",
            }:'''
    if marker in text:
        text = text.replace(marker, '''                "context",
                "learning_session",
            }:''', 1)
        changed += 1
        print("✅ added learning_session to allowed kind set")
    else:
        print("⚠️ allowed kind set marker not found, skipped allowed set")

p.write_text(text)
print(f"✅ flexible patch done, changed blocks: {changed}")
