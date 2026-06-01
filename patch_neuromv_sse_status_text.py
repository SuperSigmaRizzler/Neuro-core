from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

old = '''  if (type === "status") {
    showAssistantStatus(assistantId, data.name);
    return;
  }
'''

new = '''  if (type === "status") {
    showAssistantStatus(assistantId, {
      name: data.name,
      text: data.text || data.label || ""
    });
    return;
  }
'''

if old not in text:
    print("❌ status SSE block not found.")
    print("Kirim output: grep -n 'type === \"status\"' -A8 -B3 static/script.js")
    raise SystemExit

text = text.replace(old, new, 1)

old_func = '''function showAssistantStatus(assistantId, status) {
  const msg = findMessage(assistantId);

  if (!msg) return;

  msg.status = status === "clear" ? null : status;

  updateAssistantDom(assistantId);
  syncGuestCurrentMessages();
}
'''

new_func = '''function showAssistantStatus(assistantId, status) {
  const msg = findMessage(assistantId);

  if (!msg) return;

  const normalizedStatus = (status && typeof status === "object")
    ? {
        name: status.name || "thinking",
        text: status.text || status.label || ""
      }
    : {
        name: status || "thinking",
        text: ""
      };

  msg.status = normalizedStatus.name === "clear" ? null : normalizedStatus;

  updateAssistantDom(assistantId);
  syncGuestCurrentMessages();
}
'''

if old_func not in text:
    print("❌ showAssistantStatus function not found.")
    print("Kirim output: sed -n '1050,1090p' static/script.js")
    raise SystemExit

text = text.replace(old_func, new_func, 1)

p.write_text(text)
print("✅ SSE dynamic status text patched.")
