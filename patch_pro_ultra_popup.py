from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

# ==================================================
# 1) Replace subtitle text in existing injected menu code
# ==================================================
text = text.replace('"Deep public reasoning"', '"Our Most Powerful Model"')
text = text.replace('Deep public reasoning', 'Our Most Powerful Model')
text = text.replace('Complex thinking', 'Complex thinking')

# ==================================================
# 2) Add Pro/Ultra first-open aurora popup
# ==================================================
addon = r'''

// ==================================================
// PRO / ULTRA FIRST-OPEN AURORA INFO POPUP
// Shows once per browser session when user first selects Pro/Ultra.
// Backend daily limit still needs to enforce the real limit.
// ==================================================

function showPremiumModeInfoPopup(mode) {
  const isUltra = mode === "ultra";

  const title = isUltra
    ? "Ultra mode: Our Most Powerful Model"
    : "Pro mode: Complex Thinking";

  const subtitle = isUltra
    ? "Ultra mode uses the strongest model available in NeuroMV and is limited to 1 use per day."
    : "Pro mode uses stronger reasoning and is limited to 3 uses per day.";

  const footer = isUltra
    ? "Use it for your hardest questions, deep debugging, and complex reasoning."
    : "Use it when Flash is not enough but Ultra would be overkill.";

  const old = document.querySelector(".premium-mode-backdrop");
  if (old) old.remove();

  const wrap = document.createElement("div");
  wrap.className = "premium-mode-backdrop";
  wrap.innerHTML = `
    <div class="premium-mode-card ${isUltra ? "ultra-card" : "pro-card"}">
      <div class="premium-mode-orb" aria-hidden="true"></div>

      <div class="premium-mode-inner">
        <div class="premium-mode-badge">${isUltra ? "🌌" : "✨"}</div>

        <h2>${escapeHtml(title)}</h2>
        <p class="premium-mode-subtitle">${escapeHtml(subtitle)}</p>
        <p class="premium-mode-footer">${escapeHtml(footer)}</p>

        <button type="button" class="premium-mode-ok">Continue</button>
      </div>
    </div>
  `;

  const close = () => wrap.remove();

  wrap.addEventListener("click", (e) => {
    if (e.target === wrap) close();
  });

  const btn = wrap.querySelector(".premium-mode-ok");
  if (btn) btn.addEventListener("click", close);

  document.body.appendChild(wrap);
}

function maybeShowPremiumModeInfo(mode) {
  if (mode !== "pro" && mode !== "ultra") return;

  const key = `neuromv_seen_${mode}_info_this_session`;

  try {
    if (sessionStorage.getItem(key) === "1") return;
    sessionStorage.setItem(key, "1");
  } catch (e) {
    // If sessionStorage is blocked, still show naturally.
  }

  showPremiumModeInfoPopup(mode);
}

// Capture clicks from both original HTML mode buttons and injected Pro/Ultra buttons.
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".mode-option");
  if (!btn) return;

  const mode = btn.dataset.mode;
  if (mode === "pro" || mode === "ultra") {
    setTimeout(() => maybeShowPremiumModeInfo(mode), 80);
  }
}, true);
'''

if "function showPremiumModeInfoPopup(mode)" not in text:
    text += addon
    print("✅ Premium popup JS added.")
else:
    print("✅ Premium popup JS already exists.")

p.write_text(text)
print("✅ script.js patched.")
