from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

changed = 0

# Add global variable
if "let composerPreview = null;" not in text:
    anchor = 'let selectedFile = null;\n'
    if anchor not in text:
        print("❌ anchor selectedFile not found")
        raise SystemExit
    text = text.replace(anchor, anchor + "let composerPreview = null;\n", 1)
    changed += 1
    print("✅ composerPreview variable added")
else:
    print("ℹ️ composerPreview variable already exists")

# Add setup call in init
if "setupComposerPreview();" not in text:
    old = '''async function init() {
  applySidebarState();
  bindEvents();

  await loadMe();
  await enterApp();
  setSendIdle();
}
'''
    new = '''async function init() {
  applySidebarState();
  setupComposerPreview();
  bindEvents();

  await loadMe();
  await enterApp();
  setSendIdle();
}
'''
    if old not in text:
        print("❌ init block not found")
        raise SystemExit
    text = text.replace(old, new, 1)
    changed += 1
    print("✅ setupComposerPreview added to init")
else:
    print("ℹ️ setupComposerPreview already called")

# Add functions before bindEvents
if "function setupComposerPreview()" not in text:
    anchor = '''function setSendBusy() {
  if (!sendBtn) return;
  sendBtn.classList.add("is-stopping");
  sendBtn.textContent = "";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
}


function bindEvents() {
'''
    insert = '''function setSendBusy() {
  if (!sendBtn) return;
  sendBtn.classList.add("is-stopping");
  sendBtn.textContent = "";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
}

function setupComposerPreview() {
  if (!attachmentPreview || !input) return;

  composerPreview = document.createElement("div");
  composerPreview.id = "composerPreview";
  composerPreview.className = "composer-preview hidden";
  composerPreview.setAttribute("aria-live", "polite");

  // Put preview above textarea, below attachment card.
  attachmentPreview.insertAdjacentElement("afterend", composerPreview);
}

function renderComposerPreview() {
  if (!composerPreview || !input) return;

  const text = input.value || "";

  if (!text.trim()) {
    composerPreview.classList.add("hidden");
    composerPreview.innerHTML = "";
    return;
  }

  composerPreview.classList.remove("hidden");

  const previewContent = document.createElement("div");
  previewContent.className = "content composer-preview-content";
  previewContent.innerHTML = renderRichText(text);

  composerPreview.innerHTML = "";
  composerPreview.appendChild(previewContent);

  attachCopyButtons(composerPreview);
  enhanceRendered(composerPreview);
}


function bindEvents() {
'''
    if anchor not in text:
        print("❌ bindEvents anchor not found")
        raise SystemExit
    text = text.replace(anchor, insert, 1)
    changed += 1
    print("✅ composer preview functions added")
else:
    print("ℹ️ composer preview functions already exist")

# Replace input listener
old_listener = '''  input.addEventListener("input", autoResize);
'''
new_listener = '''  input.addEventListener("input", () => {
    autoResize();
    renderComposerPreview();
  });
'''
if old_listener in text and new_listener not in text:
    text = text.replace(old_listener, new_listener, 1)
    changed += 1
    print("✅ input listener now updates preview")
else:
    print("ℹ️ input listener already patched or not found")

# Hide preview after submit
old_clear = '''  input.value = "";
  autoResize();

  renderChat();
'''
new_clear = '''  input.value = "";
  autoResize();
  renderComposerPreview();

  renderChat();
'''
if old_clear in text and new_clear not in text:
    text = text.replace(old_clear, new_clear, 1)
    changed += 1
    print("✅ preview clears after send")
else:
    print("ℹ️ submit clear already patched or not found")

# Hide preview when resetting new chat
old_reset = '''  selectedFile = null;
  fileInput.value = "";

  renderAttachmentPreview();
'''
new_reset = '''  selectedFile = null;
  fileInput.value = "";
  input.value = "";
  autoResize();
  renderComposerPreview();

  renderAttachmentPreview();
'''
if old_reset in text and new_reset not in text:
    text = text.replace(old_reset, new_reset, 1)
    changed += 1
    print("✅ preview clears on new chat")
else:
    print("ℹ️ reset block already patched or not found")

p.write_text(text)
print(f"✅ script patch done, changed: {changed}")
