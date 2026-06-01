from pathlib import Path
import re

js_path = Path("static/script.js")
css_path = Path("static/style.css")

js = js_path.read_text()
css = css_path.read_text()

# ==================================================
# 1) Patch send idle / generating button
# ==================================================
start = js.find("function setSendIdle() {")
end = js.find("\nfunction setSendGenerating()", start)

if start != -1 and end != -1:
    new_idle = r'''function setSendIdle() {
  if (!sendBtn) return;

  sendBtn.classList.remove("is-stopping");
  sendBtn.classList.add("send-arrow");
  sendBtn.textContent = "›";
  sendBtn.title = "Send";
  sendBtn.type = "submit";
  sendBtn.onclick = null;
}

'''
    js = js[:start] + new_idle + js[end+1:]
    print("✅ setSendIdle patched.")
else:
    print("⚠️ setSendIdle not found; CSS will still polish button.")

start = js.find("function setSendGenerating() {")
end = js.find("\nfunction", start + 1)

if start != -1 and end != -1:
    new_generating = r'''function setSendGenerating() {
  if (!sendBtn) return;

  sendBtn.classList.remove("send-arrow");
  sendBtn.classList.add("is-stopping");
  sendBtn.textContent = "■";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
}

'''
    js = js[:start] + new_generating + js[end+1:]
    print("✅ setSendGenerating patched.")
else:
    print("⚠️ setSendGenerating not found; direct streamChat button state remains.")

# direct old streamChat button state cleanup
js = js.replace(
'''  sendBtn.textContent = "■";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
''',
'''  setSendGenerating();
'''
)

# ==================================================
# 2) Ensure user messages use renderPlainText(), not plain textContent
# ==================================================
# This handles common patterns without touching assistant renderer.
patterns = [
    (
        r'(\bif\s*\(\s*message\.role\s*===\s*["\']user["\']\s*\)\s*\{[\s\S]*?)(bubble\.textContent\s*=\s*message\.text\s*;)',
        r'\1bubble.innerHTML = renderPlainText(message.text || "");'
    ),
    (
        r'(\bif\s*\(\s*msg\.role\s*===\s*["\']user["\']\s*\)\s*\{[\s\S]*?)(bubble\.textContent\s*=\s*msg\.text\s*;)',
        r'\1bubble.innerHTML = renderPlainText(msg.text || "");'
    ),
    (
        r'(bubble\.classList\.add\(["\']user[\s\S]*?)(bubble\.textContent\s*=\s*text\s*;)',
        r'\1bubble.innerHTML = renderPlainText(text || "");'
    ),
]

changed_user_render = False
for pat, repl in patterns:
    new_js = re.sub(pat, repl, js, count=1)
    if new_js != js:
        js = new_js
        changed_user_render = True

# Fallback: if there is a createMessageElement with user branch using escapeHtml, preserve markdown by replacing exact common expression.
js = js.replace(
    'bubble.innerHTML = escapeHtml(message.text || "");',
    'bubble.innerHTML = renderPlainText(message.text || "");'
)
js = js.replace(
    'bubble.innerHTML = escapeHtml(msg.text || "");',
    'bubble.innerHTML = renderPlainText(msg.text || "");'
)

if changed_user_render:
    print("✅ user markdown render patched.")
else:
    print("⚠️ user render branch not confidently found; applied safe fallback replacements only.")

js_path.write_text(js)

# ==================================================
# 3) CSS polish: send button, status no bubble, user width, markdown user
# ==================================================
addon = r'''

/* ==================================================
   FINAL CHAT POLISH PATCH
   - clean > send button
   - clean square stop button
   - text-only shimmer statuses
   - user bubble max width
   - user markdown/code rendering
================================================== */

/* Send button: clean > style */
#sendBtn,
.send-btn {
  display: grid !important;
  place-items: center !important;
  width: 54px !important;
  height: 54px !important;
  min-width: 54px !important;
  border-radius: 999px !important;
  border: 0 !important;
  background: rgba(255,255,255,.94) !important;
  color: #07090f !important;
  font-size: 34px !important;
  line-height: 1 !important;
  font-weight: 520 !important;
  box-shadow:
    0 12px 28px rgba(0,0,0,.24),
    inset 0 1px 0 rgba(255,255,255,.9) !important;
  transform: none !important;
}

#sendBtn.send-arrow {
  font-family: ui-rounded, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
  padding-bottom: 4px !important;
}

#sendBtn.is-stopping,
.send-btn.is-stopping {
  background: rgba(255,255,255,.94) !important;
  color: #080a10 !important;
  font-size: 22px !important;
  font-weight: 900 !important;
  padding: 0 !important;
}

#sendBtn.is-stopping::before,
#sendBtn.is-stopping::after,
.send-btn.is-stopping::before,
.send-btn.is-stopping::after {
  display: none !important;
  content: none !important;
}

/* User bubble should not eat the whole screen */
.message.user {
  display: flex !important;
  justify-content: flex-end !important;
}

.message.user .bubble,
.user-message .bubble,
.bubble.user {
  width: fit-content !important;
  max-width: min(78vw, 680px) !important;
  overflow-wrap: anywhere !important;
  word-break: break-word !important;
}

@media (max-width: 780px) {
  .message.user .bubble,
  .user-message .bubble,
  .bubble.user {
    max-width: 82vw !important;
  }
}

/* Status-only assistant bubble should become invisible */
.message.assistant .bubble:has(.ai-status):not(:has(.content)):not(:has(.thought-time)),
.assistant-message .bubble:has(.ai-status):not(:has(.content)):not(:has(.thought-time)) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 8px 0 14px !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

/* Text-only shimmer status */
.ai-status,
.glossy-status,
.thinking-status,
.searching-status,
.image-status,
.tool-status,
.complex-status,
.ultra-public-status {
  display: inline-flex !important;
  align-items: center !important;
  width: fit-content !important;
  max-width: min(86vw, 680px) !important;
  padding: 0 !important;
  margin: 8px 0 14px !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  overflow: visible !important;
}

.glossy-status .status-shine,
.glossy-status::before {
  display: none !important;
  content: none !important;
}

.glossy-status .status-label {
  display: inline-block !important;
  max-width: min(86vw, 680px) !important;
  font-size: 15px !important;
  font-weight: 650 !important;
  line-height: 1.18 !important;
  letter-spacing: -0.018em !important;
  white-space: normal !important;

  background:
    linear-gradient(
      105deg,
      rgba(155,166,190,.58) 0%,
      rgba(245,248,255,.98) 38%,
      rgba(135,170,255,.92) 50%,
      rgba(230,238,255,.95) 62%,
      rgba(155,166,190,.58) 100%
    ) !important;
  background-size: 260% 100% !important;
  background-position: 0% 50% !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  color: transparent !important;
  text-shadow: none !important;
  animation: neuroStatusTextShimmer 2.15s ease-in-out infinite !important;
}

/* Ultra status slightly more premium, still no bubble */
.ultra-public-status .status-label {
  font-style: italic !important;
  background:
    linear-gradient(
      105deg,
      rgba(180,190,255,.62) 0%,
      rgba(255,255,255,.96) 36%,
      rgba(190,120,255,.92) 52%,
      rgba(100,220,255,.88) 68%,
      rgba(180,190,255,.62) 100%
    ) !important;
  background-size: 280% 100% !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  color: transparent !important;
}

/* Flash dot stays dot-only */
.ai-status.instant-status {
  padding: 0 !important;
  background: transparent !important;
}

.instant-dot {
  display: inline-block !important;
  width: 12px !important;
  height: 12px !important;
  border-radius: 999px !important;
  background: rgba(235,238,245,.88) !important;
  animation: neuroFlashDotScale .78s ease-in-out infinite !important;
}

/* User markdown rendering */
.message.user .bubble p,
.user-message .bubble p {
  margin: 0 0 10px !important;
}

.message.user .bubble p:last-child,
.user-message .bubble p:last-child {
  margin-bottom: 0 !important;
}

.message.user .bubble code,
.user-message .bubble code,
.bubble.user code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
  font-size: .92em !important;
  padding: .12em .35em !important;
  border-radius: 7px !important;
  background: rgba(255,255,255,.12) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
}

.message.user .bubble pre,
.user-message .bubble pre,
.bubble.user pre {
  max-width: 100% !important;
  overflow-x: auto !important;
  padding: 12px !important;
  border-radius: 13px !important;
  background: rgba(0,0,0,.28) !important;
  border: 1px solid rgba(255,255,255,.10) !important;
  margin: 10px 0 !important;
}

.message.user .bubble pre code,
.user-message .bubble pre code,
.bubble.user pre code {
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
}

/* Menu polish so Pro/Ultra subtitles do not look cramped */
.mode-option.premium-mode-option,
.mode-option {
  min-height: 58px !important;
}

.mode-option-copy small {
  white-space: normal !important;
  line-height: 1.2 !important;
}

@keyframes neuroStatusTextShimmer {
  0%, 100% { background-position: 0% 50%; opacity: .62; }
  42% { background-position: 100% 50%; opacity: 1; }
  70% { background-position: 145% 50%; opacity: .76; }
}

@keyframes neuroFlashDotScale {
  0%, 100% { transform: scale(.68); }
  50% { transform: scale(1.22); }
}

@media (prefers-reduced-motion: reduce) {
  .glossy-status .status-label,
  .instant-dot {
    animation: none !important;
  }
}
'''

if "FINAL CHAT POLISH PATCH" not in css:
    css += addon
    print("✅ CSS polish appended.")
else:
    print("✅ CSS polish already exists.")

css_path.write_text(css)

print("Patch done ✅")
