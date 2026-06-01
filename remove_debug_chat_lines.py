from pathlib import Path

p = Path("app.py")
text = p.read_text()

lines = text.splitlines()
new_lines = []
removed = 0

for line in lines:
    if "DEBUG_CHAT:" in line:
        removed += 1
        continue
    new_lines.append(line)

p.write_text("\n".join(new_lines) + "\n")
print(f"✅ Removed {removed} DEBUG_CHAT lines from app.py")
