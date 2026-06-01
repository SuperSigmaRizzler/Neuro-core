from pathlib import Path
import re

p = Path("static/script.js")
text = p.read_text()

# Replace setSendIdle with CSS-drawn arrow
text = re.sub(
    r'''function setSendIdle\(\) \{[\s\S]*?\n\}''',
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

# Replace setSendGenerating with CSS-drawn stop square
text = re.sub(
    r'''function setSendGenerating\(\) \{[\s\S]*?\n\}''',
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

# Remove any direct raw arrows/squares if still present
text = text.replace('sendBtn.textContent = ">";', 'sendBtn.textContent = "";')
text = text.replace('sendBtn.innerHTML = "&gt;";', 'sendBtn.innerHTML = "";')
text = text.replace('sendBtn.textContent = "■";', 'sendBtn.textContent = "";')
text = text.replace('sendBtn.innerHTML = "■";', 'sendBtn.innerHTML = "";')

p.write_text(text)
print("✅ JS send button now uses CSS icon, not raw text.")
