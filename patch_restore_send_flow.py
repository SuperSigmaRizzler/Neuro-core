from pathlib import Path
import re

p = Path("static/script.js")
text = p.read_text()

# 1) Remove emergency click rescue block completely
marker = "// EMERGENCY SEND CLICK RESCUE"
idx = text.find(marker)

if idx != -1:
    start = text.rfind("// ==================================================", 0, idx)
    end = text.find("})();", idx)

    if start != -1 and end != -1:
        end += len("})();")
        text = text[:start] + "\n\n" + text[end:]
        print("✅ Removed emergency send click rescue.")
    else:
        print("⚠️ Found marker but block boundaries not found.")
else:
    print("✅ No emergency send click rescue found.")

# 2) Restore send idle function: normal submit button, CSS icon handles look
text = re.sub(
    r"function setSendIdle\(\) \{[\s\S]*?\n\}",
    '''function setSendIdle() {
  if (!sendBtn) return;

  sendBtn.classList.remove("is-stopping");
  sendBtn.classList.add("send-arrow");
  sendBtn.textContent = "";
  sendBtn.innerHTML = "";
  sendBtn.title = "Send";
  sendBtn.type = "submit";
  sendBtn.onclick = null;
}''',
    text,
    count=1
)

# 3) Restore generating button: stop button only, no mixed state
text = re.sub(
    r"function setSendGenerating\(\) \{[\s\S]*?\n\}",
    '''function setSendGenerating() {
  if (!sendBtn) return;

  sendBtn.classList.remove("send-arrow");
  sendBtn.classList.add("is-stopping");
  sendBtn.textContent = "";
  sendBtn.innerHTML = "";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
}''',
    text,
    count=1
)

p.write_text(text)
print("✅ Send flow restored to normal form submit.")
