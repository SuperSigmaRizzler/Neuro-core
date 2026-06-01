from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

# Replace updateAssistantDom only
start = text.find("function updateAssistantDom(assistantId) {")
end = text.find("function createStatusElement(status) {", start)

if start == -1 or end == -1:
    print("❌ updateAssistantDom block not found.")
    print("Kirim output: grep -n \"function updateAssistantDom\\|function createStatusElement\" static/script.js")
    raise SystemExit

new_update = r'''function updateAssistantDom(assistantId) {
  const msg = findMessage(assistantId);
  const el = chatBox.querySelector(`[data-id="${assistantId}"]`);

  if (!msg || !el) return;

  const bubble = el.querySelector(".bubble");
  if (!bubble) return;

  try {
    bubble.classList.toggle("streaming-bubble", !!streamTimers[assistantId]);
    bubble.innerHTML = "";

    if (msg.status) {
      bubble.appendChild(createStatusElement(msg.status));
    }

    if (msg.thoughtSeconds) {
      const thought = document.createElement("div");
      thought.className = "thought-time";
      thought.textContent = formatThoughtTime(msg.thoughtSeconds);
      bubble.appendChild(thought);
    }

    const content = document.createElement("div");
    content.className = "content";

    try {
      content.innerHTML = renderRichText(msg.text || "");
    } catch (err) {
      // Fallback: never let markdown/render errors kill streaming UI.
      content.textContent = msg.text || "";
    }

    bubble.appendChild(content);

    try {
      attachCopyButtons(bubble);
    } catch {}

    try {
      enhanceRendered(bubble);
    } catch {}

  } catch (err) {
    // Last-resort fallback: show plain text instead of freezing the UI.
    bubble.textContent = msg.text || "";
  }
}

'''

text = text[:start] + new_update + text[end:]

# Make SSE done event unlock UI immediately
old_done = '''  if (type === "done") {
    clearAssistantStatus(assistantId);

    if (currentUser) loadChats();
    else syncGuestCurrentMessages();
  }
}'''

new_done = '''  if (type === "done") {
    clearAssistantStatus(assistantId);

    // Flush any remaining queued text before unlocking UI.
    const rest = streamQueues[assistantId] || "";
    if (rest) {
      clearAssistantStreamQueue(assistantId);
      appendAssistantTextImmediate(assistantId, rest);
    }

    if (currentUser) loadChats();
    else syncGuestCurrentMessages();

    finishGeneration();
    return;
  }
}'''

if old_done in text:
    text = text.replace(old_done, new_done, 1)
    print("✅ done handler patched.")
else:
    print("⚠️ done handler exact block not found; updateAssistantDom still patched.")

p.write_text(text)
print("✅ Frontend render failsafe installed.")
