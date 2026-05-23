from pathlib import Path

p = Path("app.py")
lines = p.read_text(encoding="utf-8").splitlines()

new_lines = []
i = 0
fixed = False

while i < len(lines):
    line = lines[i]

    if line.strip() == "brain_context =":
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + 'brain_context = ""')
        fixed = True
        i += 1

        # Skip leftover broken arguments until the closing ")" line.
        while i < len(lines):
            if lines[i].strip() == ")":
                i += 1
                break
            i += 1

        continue

    new_lines.append(line)
    i += 1

p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

if fixed:
    print("✅ Fixed broken brain_context block.")
else:
    print("⚠️ Did not find broken 'brain_context =' line.")
