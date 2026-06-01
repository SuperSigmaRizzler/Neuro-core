from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

# ==================================================
# 1) Ensure setMode supports instant/thinking/pro/ultra
# ==================================================
start = text.find("function setMode(mode, save = true) {")
end = text.find("\nfunction renderHistory()", start)

if start == -1 or end == -1:
    print("❌ setMode block not found.")
    raise SystemExit

new_set_mode = r'''function setMode(mode, save = true) {
  const allowedModes = ["instant", "thinking", "pro", "ultra"];
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
  } else if (currentMode === "ultra") {
    modePickerLabel.textContent = "🌌 Ultra";
    modeText.textContent = "Ultra mode";
  } else {
    modePickerLabel.textContent = "⚡ Flash";
    modeText.textContent = "Flash mode";
  }

  if (save) {
    localStorage.setItem(STORAGE_MODE, currentMode);
  }
}

'''

text = text[:start] + new_set_mode + text[end+1:]


# ==================================================
# 2) Add Pro / Ultra buttons into mode menu if missing
# ==================================================
addon = r'''

// ==================================================
// PRO / ULTRA MODE OPTIONS
// Adds missing menu buttons without requiring HTML rewrite.
// ==================================================
function ensurePremiumModeOptions() {
  if (!modeMenu) return;

  const existingPro = modeMenu.querySelector('.mode-option[data-mode="pro"]');
  const existingUltra = modeMenu.querySelector('.mode-option[data-mode="ultra"]');

  function makeModeButton(mode, icon, title, subtitle) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mode-option premium-mode-option";
    btn.dataset.mode = mode;
    btn.innerHTML = `
      <span class="mode-option-icon">${icon}</span>
      <span class="mode-option-copy">
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(subtitle)}</small>
      </span>
    `;

    btn.addEventListener("click", () => {
      setMode(mode, true);
      modeMenu.classList.add("hidden");
    });

    return btn;
  }

  if (!existingPro) {
    modeMenu.appendChild(makeModeButton(
      "pro",
      "✨",
      "Pro",
      "Complex thinking"
    ));
  }

  if (!existingUltra) {
    modeMenu.appendChild(makeModeButton(
      "ultra",
      "🌌",
      "Ultra",
      "Deep public reasoning"
    ));
  }

  setMode(currentMode, false);
}

ensurePremiumModeOptions();
'''

if "function ensurePremiumModeOptions()" not in text:
    text += addon
    print("✅ Pro/Ultra menu injector added.")
else:
    print("✅ Pro/Ultra menu injector already exists.")

p.write_text(text)
print("✅ static/script.js patched.")
