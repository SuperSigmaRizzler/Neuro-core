from pathlib import Path

p = Path("core/limits.py")
text = p.read_text()

old = '''def format_limit_error(error: LimitError) -> str:
    info = getattr(error, "info", {}) or {}
    kind = info.get("kind", "usage")
    limit = info.get("limit", "?")
    return f"Limit {kind} hari ini sudah habis. Batasnya {limit}/day."
'''

new = '''def format_limit_error(error: LimitError) -> str:
    # User-facing message only.
    # Do not expose exact daily limits/counts in UI.
    return "You've reached your usage limit. Please try again later."
'''

if old not in text:
    print("❌ format_limit_error block not found")
    print("Run: sed -n '1,80p' core/limits.py")
    raise SystemExit

text = text.replace(old, new, 1)
p.write_text(text)
print("✅ core/limits.py professional limit message patched")
