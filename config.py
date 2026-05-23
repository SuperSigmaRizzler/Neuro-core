import os
from dotenv import load_dotenv

load_dotenv()


def split_values(*names):
    values = []

    for name in names:
        raw = os.getenv(name, "").strip()
        if not raw:
            continue

        for item in raw.split(","):
            value = item.strip()
            if value:
                values.append(value)

    clean = []
    seen = set()

    for value in values:
        if value not in seen:
            clean.append(value)
            seen.add(value)

    return clean


def env_bool(name, default=False):
    raw = os.getenv(name, "").strip().lower()

    if not raw:
        return default

    return raw in ["1", "true", "yes", "on"]


def env_int(name, default):
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


# =========================
# APP
# =========================

APP_NAME = os.getenv("APP_NAME", "NeuroMV")
SECRET_KEY = os.getenv("SECRET_KEY", "neuromv-core-secret")
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)

# =========================
# STORAGE
# =========================

MEMORY_FILE = os.getenv("MEMORY_FILE", "data/chat_memory.json").strip()
FACTS_FILE = os.getenv("FACTS_FILE", "data/facts.json").strip()
DB_FILE = os.getenv("DB_FILE", "data/neuromv.db").strip()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads").strip()

# =========================
# PROVIDERS
# =========================

GROQ_API_KEYS = split_values("GROQ_API_KEYS", "GROQ_API_KEY")
GEMINI_API_KEYS = split_values("GEMINI_API_KEYS", "GEMINI_API_KEY")
CEREBRAS_API_KEYS = split_values("CEREBRAS_API_KEYS", "CEREBRAS_API_KEY")

CLOUDFLARE_ACCOUNT_IDS = split_values(
    "CLOUDFLARE_ACCOUNT_IDS",
    "CLOUDFLARE_ACCOUNT_ID"
)

CLOUDFLARE_API_TOKENS = split_values(
    "CLOUDFLARE_API_TOKENS",
    "CLOUDFLARE_API_TOKEN"
)

MISTRAL_API_KEYS = split_values("MISTRAL_API_KEYS", "MISTRAL_API_KEY")

SERPAPI_API_KEYS = split_values("SERPAPI_API_KEYS", "SERPAPI_API_KEY")
SERPER_API_KEYS = split_values("SERPER_API_KEYS", "SERPER_API_KEY")
TAVILY_API_KEYS = split_values("TAVILY_API_KEYS", "TAVILY_API_KEY")

# Optional/future slots. Do not treat as active unless user fills/uses them.
DEEPSEEK_API_KEYS = split_values("DEEPSEEK_API_KEYS", "DEEPSEEK_API_KEY")
TOGETHER_API_KEYS = split_values("TOGETHER_API_KEYS", "TOGETHER_API_KEY")
OPENROUTER_API_KEYS = split_values("OPENROUTER_API_KEYS", "OPENROUTER_API_KEY")
REPLICATE_API_TOKENS = split_values("REPLICATE_API_TOKENS", "REPLICATE_API_TOKEN")

# =========================
# MODE / MODEL SETTINGS
# =========================

INSTANT_PROVIDER = os.getenv("INSTANT_PROVIDER", "groq").strip().lower()
THINKING_PROVIDER = os.getenv("THINKING_PROVIDER", "groq").strip().lower()

INSTANT_MODEL = os.getenv("INSTANT_MODEL", "llama-3.1-8b-instant").strip()
THINKING_MODEL = os.getenv("THINKING_MODEL", "openai/gpt-oss-120b").strip()

# =========================
# RUNTIME
# =========================

MAX_RECENT_MESSAGES = env_int("MAX_RECENT_MESSAGES", 20)
REQUEST_TIMEOUT = env_int("REQUEST_TIMEOUT", 60)
MAX_PROVIDER_ATTEMPTS = env_int("MAX_PROVIDER_ATTEMPTS", 10)

MAX_CONTEXT_CHARS = env_int("MAX_CONTEXT_CHARS", 24000)

# =========================
# LIMITS
# =========================

DAILY_LIMIT = env_int("DAILY_LIMIT", 100)
UPLOAD_LIMIT = env_int("UPLOAD_LIMIT", 10)
FILE_LIMIT = env_int("FILE_LIMIT", 5)
IMAGE_LIMIT = env_int("IMAGE_LIMIT", 5)
SEARCH_LIMIT = env_int("SEARCH_LIMIT", 50)
URL_LIMIT = env_int("URL_LIMIT", 50)
OCR_LIMIT = env_int("OCR_LIMIT", 20)
VISION_LIMIT = env_int("VISION_LIMIT", 20)

MAX_UPLOAD_MB = env_int("MAX_UPLOAD_MB", 15)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# =========================
# FILE TYPE SUPPORT
# =========================

TEXT_EXTS = {
    ".txt", ".md", ".json", ".csv", ".py", ".js", ".html", ".css",
    ".xml", ".yml", ".yaml", ".sql", ".log", ".java", ".cpp", ".c",
    ".php", ".rb", ".go", ".rs", ".ts", ".tsx", ".jsx"
}

IMAGE_EXTS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"
}

PDF_EXTS = {
    ".pdf"
}

ALLOWED_UPLOAD_EXTS = TEXT_EXTS | IMAGE_EXTS | PDF_EXTS

CHAT_COOLDOWN_SECONDS = env_int("CHAT_COOLDOWN_SECONDS", 3)

# ==================================================
# PREMIUM / LIMITED MODES
# ==================================================
PRO_PROVIDER = "gemini"
PRO_MODEL = "gemini-2.5-flash"
PRO_DAILY_LIMIT = 3

GOD_PROVIDER = "gemini"
GOD_MODEL = "gemini-2.5-pro"
GOD_DAILY_LIMIT = 1
