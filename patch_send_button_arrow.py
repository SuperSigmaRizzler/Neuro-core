from pathlib import Path
import re

p = Path("static/script.js")
text = p.read_text()

# Force idle send button to >
text = re.sub(
    r'''function setSendIdle\(\) \{[\s\S]*?\n\}''',
    '''function setSendIdle() {
  if (!sendBtn) return;

  sendBtn.classList.remove("is-stopping");
  sendBtn.classList.add("send-arrow");
  sendBtn.textContent = ">";
  sendBtn.innerHTML = "&gt;";
  sendBtn.title = "Send";
  sendBtn.type = "submit";
  sendBtn.onclick = null;
}''',
    text,
    count=1
)

# Force generating button to clean square
text = re.sub(
    r'''function setSendGenerating\(\) \{[\s\S]*?\n\}''',
    '''function setSendGenerating() {
  if (!sendBtn) return;

  sendBtn.classList.remove("send-arrow");
  sendBtn.classList.add("is-stopping");
  sendBtn.textContent = "■";
  sendBtn.innerHTML = "■";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
}''',
    text,
    count=1
)

# Replace direct old assignments too
text = text.replace('sendBtn.textContent = "↑";', 'sendBtn.textContent = ">";')
text = text.replace('sendBtn.innerHTML = "↑";', 'sendBtn.innerHTML = "&gt;";')
text = text.replace('sendBtn.textContent = "^";', 'sendBtn.textContent = ">";')
text = text.replace('sendBtn.innerHTML = "^";', 'sendBtn.innerHTML = "&gt;";')
text = text.replace('sendBtn.textContent = "›";', 'sendBtn.textContent = ">";')
text = text.replace('sendBtn.innerHTML = "›";', 'sendBtn.innerHTML = "&gt;";')

p.write_text(text)
print("✅ send button JS forced to > / stop square.")
