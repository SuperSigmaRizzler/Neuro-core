from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

addon = r'''

// ==================================================
// EMERGENCY SEND CLICK RESCUE
// Ensures send button submits when idle.
// ==================================================
(function rescueSendButtonClick() {
  if (!sendBtn || !form) return;

  sendBtn.addEventListener("click", (e) => {
    if (sendBtn.classList.contains("is-stopping")) {
      return;
    }

    if (typeof isGenerating !== "undefined" && isGenerating) {
      return;
    }

    e.preventDefault();

    if (form.requestSubmit) {
      form.requestSubmit();
    } else {
      form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
  });
})();
'''

if "EMERGENCY SEND CLICK RESCUE" not in text:
    text += addon
    p.write_text(text)
    print("✅ send click rescue added.")
else:
    print("✅ send click rescue already exists.")
