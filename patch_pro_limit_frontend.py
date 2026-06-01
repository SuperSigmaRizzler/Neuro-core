from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

changed = 0

# Add limitLocked state
if "let limitLocked = false;" not in text:
    anchor = "let activeController = null;\n"
    if anchor not in text:
        print("❌ activeController anchor not found")
        raise SystemExit
    text = text.replace(anchor, anchor + "let limitLocked = false;\n", 1)
    changed += 1
    print("✅ limitLocked state added")

# Patch setSendIdle
old_idle = '''function setSendIdle() {
  if (!sendBtn) return;
  sendBtn.classList.remove("is-stopping");
  sendBtn.textContent = "";
  sendBtn.title = "Send";
  sendBtn.type = "submit";
  sendBtn.onclick = null;
}
'''

new_idle = '''function setSendIdle() {
  if (!sendBtn) return;

  sendBtn.classList.remove("is-stopping");
  sendBtn.textContent = "";

  if (limitLocked) {
    sendBtn.disabled = true;
    sendBtn.classList.add("limit-locked");
    sendBtn.title = "Usage limit reached";
    sendBtn.type = "button";
    sendBtn.onclick = null;
    return;
  }

  sendBtn.disabled = false;
  sendBtn.classList.remove("limit-locked");
  sendBtn.title = "Send";
  sendBtn.type = "submit";
  sendBtn.onclick = null;
}
'''

if old_idle in text:
    text = text.replace(old_idle, new_idle, 1)
    changed += 1
    print("✅ setSendIdle patched")
else:
    print("ℹ️ setSendIdle already patched or not found")

# Insert popup functions before bindEvents
if "function showLimitPopup(" not in text:
    anchor = "function bindEvents() {\n"
    if anchor not in text:
        print("❌ bindEvents anchor not found")
        raise SystemExit

    funcs = '''function lockLimitUI() {
  limitLocked = true;

  if (sendBtn) {
    sendBtn.disabled = true;
    sendBtn.classList.add("limit-locked");
    sendBtn.title = "Usage limit reached";
    sendBtn.type = "button";
    sendBtn.onclick = null;
  }

  if (input) {
    input.classList.add("limit-locked");
  }
}

function showLimitPopup(message = "You've reached your usage limit. Please try again later.") {
  lockLimitUI();

  let modal = document.getElementById("limitModal");

  if (!modal) {
    modal = document.createElement("div");
    modal.id = "limitModal";
    modal.className = "limit-modal hidden";
    modal.innerHTML = `
      <div class="limit-card" role="dialog" aria-modal="true" aria-labelledby="limitTitle">
        <div class="limit-icon">!</div>
        <h2 id="limitTitle">You've reached your usage limit</h2>
        <p>${escapeHtml(message)}</p>
        <button type="button" id="limitOkBtn">OK</button>
      </div>
    `;
    document.body.appendChild(modal);

    const okBtn = modal.querySelector("#limitOkBtn");
    if (okBtn) {
      okBtn.addEventListener("click", () => {
        modal.classList.add("hidden");
      });
    }

    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.add("hidden");
      }
    });
  } else {
    const msg = modal.querySelector("p");
    if (msg) msg.textContent = message;
  }

  modal.classList.remove("hidden");
}

'''
    text = text.replace(anchor, funcs + anchor, 1)
    changed += 1
    print("✅ limit popup functions added")

# Patch enter keydown
old_key = '''  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !isMobile()) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
'''

new_key = '''  input.addEventListener("keydown", e => {
    if (limitLocked && e.key === "Enter") {
      e.preventDefault();
      showLimitPopup();
      return;
    }

    if (e.key === "Enter" && !e.shiftKey && !isMobile()) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
'''

if old_key in text:
    text = text.replace(old_key, new_key, 1)
    changed += 1
    print("✅ Enter key lock patched")
else:
    print("ℹ️ keydown block already patched or not found")

# Patch handleSubmit guard
old_guard = '''  if ((!text && !selectedFile) || isGenerating) return;
'''

new_guard = '''  if (limitLocked) {
    showLimitPopup();
    return;
  }

  if ((!text && !selectedFile) || isGenerating) return;
'''

if old_guard in text:
    text = text.replace(old_guard, new_guard, 1)
    changed += 1
    print("✅ handleSubmit limit guard patched")
else:
    print("ℹ️ handleSubmit guard already patched or not found")

# Patch non-stream HTTP error handling
old_http = '''      try {
        const data = await response.json();
        msg = data.error || msg;
      } catch {}

      throw new Error(msg);
'''

new_http = '''      try {
        const data = await response.json();
        msg = data.error || msg;

        if (data.code === "limit_reached" || data.lock) {
          showLimitPopup(msg);
          return;
        }
      } catch {}

      throw new Error(msg);
'''

if old_http in text:
    text = text.replace(old_http, new_http, 1)
    changed += 1
    print("✅ HTTP limit error popup patched")
else:
    print("ℹ️ HTTP error block already patched or not found")

# Patch SSE error handling
old_sse = '''  if (type === "error") {
    clearAssistantStatus(assistantId);
    appendAssistantText(assistantId, `⚠️ ${data.message || "Terjadi error."}`);
    return;
  }
'''

new_sse = '''  if (type === "error") {
    clearAssistantStatus(assistantId);

    if (data.code === "limit_reached" || data.lock) {
      showLimitPopup(data.message || "You've reached your usage limit. Please try again later.");
      return;
    }

    appendAssistantText(assistantId, `⚠️ ${data.message || "Terjadi error."}`);
    return;
  }
'''

if old_sse in text:
    text = text.replace(old_sse, new_sse, 1)
    changed += 1
    print("✅ SSE limit error popup patched")
else:
    print("ℹ️ SSE error block already patched or not found")

p.write_text(text)
print(f"✅ frontend patch complete, changed: {changed}")
