from pathlib import Path
import os

ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "data" / "docs"
INDEX_DIR = ROOT / "index"
FAISS_PATH = INDEX_DIR / "faiss.index"
META_PATH = INDEX_DIR / "chunks.json"

# Multilingual embedding model used for local RAG retrieval.
EMBED_MODEL = "intfloat/multilingual-e5-small"

# Chunking (words)
CHUNK_WORDS = 180
CHUNK_OVERLAP = 40

# Retrieval
TOP_K = 4
MIN_SCORE = 0.78

# LLM API (OpenAI-compatible endpoint). Keep credentials in environment variables.
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TOKEN_PARAM = os.getenv("LLM_TOKEN_PARAM", "max_tokens")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "400"))
LLM_TEMP = float(os.getenv("LLM_TEMP", "0.2"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))

# --- service options ---
LLM_ENABLED = os.getenv("LLM_ENABLED", "1") == "1"        # set LLM_ENABLED=0 to force retrieval-only (no internet) mode
SERVICE_KEY = os.getenv("AI_CORE_KEY", "")                # if set, callers must send header X-API-Key
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
SCHEMES_PATH = ROOT / "data" / "schemes.json"
