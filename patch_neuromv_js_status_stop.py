from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

# ==================================================
# 1) Patch setMode(): support instant/thinking/pro/god
# ==================================================
start = text.find("function setMode(mode, save = true) {")
end = text.find("\nfunction renderHistory()", start)

if start == -1 or end == -1:
    print("❌ setMode block not found.")
else:
    new_func = r'''function setMode(mode, save = true) {
  const allowedModes = ["instant", "thinking", "pro", "god"];
  currentMode = allowedModes.includes(mode) ? mode : "instant";

  document.querySelectorAll(".mode-option").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.mode === currentMode);
  });

  if (currentMode === "thinking") {
    modePickerLabel.textContent = "🔍 Deep Analysis";
    modeText.textContent = "Thinking mode";
  } else if (currentMode === "pro") {
    modePickerLabel.textContent = "✨ Pro";
    modeText.textContent = "Pro mode";
  } else if (currentMode === "god") {
    modePickerLabel.textContent = "👑 GOD";
    modeText.textContent = "GOD mode";
  } else {
    modePickerLabel.textContent = "⚡ Flash";
    modeText.textContent = "Flash mode";
  }

  if (save) {
    localStorage.setItem(STORAGE_MODE, currentMode);
  }
}

'''
    text = text[:start] + new_func + text[end+1:]
    print("✅ setMode patched.")

# ==================================================
# 2) Patch createStatusElement(): custom backend status text
# ==================================================
start = text.find("function createStatusElement(status) {")
end = text.find("\nfunction stopGenerating()", start)

if start == -1 or end == -1:
    print("❌ createStatusElement block not found.")
else:
    new_func = r'''function createStatusElement(status) {
  const data = (status && typeof status === "object")
    ? status
    : { name: status };

  const name = data.name || "thinking";
  const customText = data.text || data.label || "";

  const el = document.createElement("div");

  // Flash only: big-small dot.
  if (name === "instant") {
    el.className = "ai-status instant-status";
    el.innerHTML = `<span class="instant-dot"></span>`;
    return el;
  }

  const labelMap = {
    thinking: "Thinking",
    searching: "Searching",
    creating_image: "Creating Image",
    reading_file: "Reading File",
    reading_pdf: "Reading PDF",
    reading_url: "Reading URL",
    analyzing_image: "Analyzing Image",
    complex_thinking: "Complex Thinking...",
    god_public_thinking: "Thinking deeper..."
  };

  const classMap = {
    thinking: "thinking-status",
    searching: "searching-status",
    creating_image: "image-status",
    reading_file: "tool-status",
    reading_pdf: "tool-status",
    reading_url: "tool-status",
    analyzing_image: "image-status",
    complex_thinking: "complex-status",
    god_public_thinking: "god-public-status"
  };

  const label = customText || labelMap[name] || "Thinking";

  el.className = `ai-status glossy-status ${classMap[name] || "thinking-status"}`;
  el.innerHTML = `
    <span class="status-shine"></span>
    <span class="status-label">${escapeHtml(label)}</span>
  `;

  return el;
}

'''
    text = text[:start] + new_func + text[end+1:]
    print("✅ createStatusElement patched.")

# ==================================================
# 3) Patch stopGenerating(): keep partial generated text
# ==================================================
start = text.find("function stopGenerating() {")
end = text.find("\nfunction finishGeneration()", start)

if start == -1 or end == -1:
    print("❌ stopGenerating block not found.")
else:
    new_func = r'''function stopGenerating() {
  if (activeController) {
    activeController.abort();
  }

  if (activeAssistantId) {
    clearAssistantStatus(activeAssistantId);
  }

  // Keep the partial assistant text exactly as-is.
  // Do not remove the bubble.
  // Do not append "Stopped."
  // Do not render the chat from scratch.
  finishGeneration();
}

'''
    text = text[:start] + new_func + text[end+1:]
    print("✅ stopGenerating patched.")

p.write_text(text)
print("JS status/stop patch done ✅")
