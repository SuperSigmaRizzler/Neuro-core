from pathlib import Path

p = Path("static/script.js")
text = p.read_text()

# -----------------------------
# Add title sanitizer before makeTitle()
# -----------------------------
old_make = '''function makeTitle(text) {
  const clean = String(text || "").replace(/\\s+/g, " ").trim();
  return clean.length > 34 ? clean.slice(0, 34) + "..." : clean || "New Chat";
}
'''

new_make = '''function sanitizeChatTitle(value, fallback = "New Chat") {
  let clean = String(value || "").replace(/\\s+/g, " ").trim();

  const badTitles = new Set([
    "{text}",
    "${text}",
    "$text",
    "undefined",
    "null",
    "none",
    "[object Object]"
  ]);

  if (!clean || badTitles.has(clean.toLowerCase())) {
    return fallback;
  }

  clean = clean
    .replace(/^["'`]+|["'`]+$/g, "")
    .replace(/^title\\s*[:=-]\\s*/i, "")
    .trim();

  if (!clean || badTitles.has(clean.toLowerCase())) {
    return fallback;
  }

  return clean.length > 42 ? clean.slice(0, 42).trim() + "..." : clean;
}

function makeTitle(text) {
  return sanitizeChatTitle(text, "New Chat");
}
'''

if old_make not in text:
    print("❌ makeTitle block not found")
    print("Run: sed -n '1380,1405p' static/script.js")
    raise SystemExit

text = text.replace(old_make, new_make, 1)

# -----------------------------
# Sanitize rendered history title
# -----------------------------
text = text.replace(
'''    titleBtn.textContent = chat.title || "New Chat";''',
'''    titleBtn.textContent = sanitizeChatTitle(chat.title, "New Chat");''',
1
)

# -----------------------------
# Sanitize openChat title
# -----------------------------
text = text.replace(
'''  currentChatTitle = chat.title || "New Chat";''',
'''  currentChatTitle = sanitizeChatTitle(chat.title, "New Chat");''',
1
)

# -----------------------------
# Sanitize meta title from backend
# -----------------------------
text = text.replace(
'''    if (data.title) {
      currentChatTitle = data.title;
      chatTitle.textContent = data.title;
    }
''',
'''    if (data.title) {
      currentChatTitle = sanitizeChatTitle(data.title, currentChatTitle || "New Chat");
      chatTitle.textContent = currentChatTitle;
    }
''',
1
)

# -----------------------------
# Replace enhanceRendered with retry-safe MathJax.
# -----------------------------
old_enhance = '''function enhanceRendered(root = document) {
  try {
    if (window.Prism) {
      window.Prism.highlightAllUnder(root);
    }
  } catch {}

  try {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([root]);
    }
  } catch {}
}
'''

new_enhance = '''function enhanceRendered(root = document) {
  try {
    if (window.Prism) {
      window.Prism.highlightAllUnder(root);
    }
  } catch {}

  typesetMath(root);
}

function typesetMath(root = document, attempt = 0) {
  try {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetClear?.([root]);
      window.MathJax.typesetPromise([root]).catch(() => {});
      return;
    }
  } catch {}

  // MathJax is loaded with defer, so early chat renders may happen before it is ready.
  // Retry briefly instead of leaving LaTeX raw forever.
  if (attempt < 8) {
    setTimeout(() => typesetMath(root, attempt + 1), 250);
  }
}
'''

if old_enhance not in text:
    print("❌ enhanceRendered block not found")
    print("Run: sed -n '790,820p' static/script.js")
    raise SystemExit

text = text.replace(old_enhance, new_enhance, 1)

p.write_text(text)
print("✅ static/script.js title + MathJax patch applied")
