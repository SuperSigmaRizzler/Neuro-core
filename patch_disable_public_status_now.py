from pathlib import Path

p = Path("app.py")
text = p.read_text()

start = text.find("            # -----------------------------\n            # Public reasoning status for Pro/Ultra.")
end = text.find("            # -----------------------------\n            # Stream model response.", start + 1)

if start == -1 or end == -1:
    print("❌ Public status block not found.")
    print("Kirim output: sed -n '890,930p' app.py")
    raise SystemExit

replacement = '''            # -----------------------------
            # Public reasoning status disabled temporarily for stability.
            # Pro/Ultra UI can still be selected, but no extra pre-model call runs here.
            # -----------------------------
'''

text = text[:start] + replacement + text[end:]

p.write_text(text)
print("✅ Public Pro/Ultra pre-status disabled temporarily.")
