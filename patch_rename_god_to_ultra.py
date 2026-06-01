from pathlib import Path

files = [
    "static/script.js",
    "static/style.css",
    "templates/index.html",
    "app.py",
    "config.py",
    "core/mode_limits.py",
    "core/public_status.py",
    "providers/router.py",
]

replacements = [
    # mode ids / statuses
    ("god_public_thinking", "ultra_public_thinking"),
    ("god-status", "ultra-status"),
    ("god-public-status", "ultra-public-status"),
    ('"god"', '"ultra"'),
    ("'god'", "'ultra'"),

    # UI labels
    ("👑 GOD", "🌌 Ultra"),
    ("GOD mode", "Ultra mode"),
    ("GOD Mode", "Ultra Mode"),
    ("GOD", "Ultra"),

    # config/env names if already added
    ("GOD_PROVIDER", "ULTRA_PROVIDER"),
    ("GOD_MODEL", "ULTRA_MODEL"),
    ("GOD_DAILY_LIMIT", "ULTRA_DAILY_LIMIT"),

    # CSS class remnants
    (".god-public-status", ".ultra-public-status"),
    (".god-status", ".ultra-status"),
]

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()

    old_text = text
    for old, new in replacements:
        text = text.replace(old, new)

    if text != old_text:
        p.write_text(text)
        print(f"✅ patched {file}")
    else:
        print(f"— no change {file}")

print("Rename GOD → Ultra done ✅")
