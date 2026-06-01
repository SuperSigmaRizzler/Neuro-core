from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

replacements = [
(
'''async function streamChat(message, chatId, assistantId, file) {
  isGenerating = true;

  sendBtn.textContent = "■";
  sendBtn.title = "Stop generating";
  sendBtn.type = "button";
  sendBtn.onclick = stopGenerating;
''',
'''async function streamChat(message, chatId, assistantId, file) {
  isGenerating = true;

  setSendBusy();
'''
),
(
'''  if (type === "token") {
    clearAssistantStatus(assistantId);
    appendAssistantText(assistantId, data.text || "");
    return;
  }
''',
'''  if (type === "token") {
    const msg = findMessage(assistantId);

    if (msg) {
      msg.status = null;
    }

    // Direct render first: avoids frontend queue/timer getting stuck.
    appendAssistantTextImmediate(assistantId, data.text || "");
    return;
  }
'''
),
(
'''  if (type === "done") {
    clearAssistantStatus(assistantId);

    // Flush remaining frontend stream queue before unlocking.
    const rest = streamQueues[assistantId] || "";
    if (rest) {
      clearAssistantStreamQueue(assistantId);
      appendAssistantTextImmediate(assistantId, rest);
    }

    if (currentUser) loadChats();
    else syncGuestCurrentMessages();

    // Important: unlock UI as soon as SSE says done.
    finishGeneration();
    return;
  }
}''',
'''  if (type === "done") {
    const msg = findMessage(assistantId);

    if (msg) {
      msg.status = null;
      updateAssistantDom(assistantId);
    }

    clearAssistantStreamQueue(assistantId);

    // Unlock UI immediately so New Chat/history are never trapped.
    finishGeneration();

    try {
      if (currentUser) loadChats();
      else syncGuestCurrentMessages();
    } catch (err) {
      console.warn("Final sync failed, but UI was unlocked:", err);
    }

    return;
  }
}'''
),
(
'''function finishGeneration() {
  isGenerating = false;
  activeController = null;
  activeAssistantId = null;

  setSendIdle();
  sendBtn.title = "Send";
  sendBtn.type = "submit";
  sendBtn.onclick = null;
}''',
'''function finishGeneration() {
  isGenerating = false;
  activeController = null;
  activeAssistantId = null;

  setSendIdle();
}'''
)
]

changed = 0

for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)
        changed += 1
    else:
        print("⚠️ block not found, skipped one replacement.")

p.write_text(text)
print(f"✅ Stream lock fix patched blocks: {changed}/{len(replacements)}")
