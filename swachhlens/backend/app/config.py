"""Runtime configuration loaded from environment variables (.env)."""
import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
STATIC_DIR = BASE_DIR.parent                                # frontend root
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Railway/Heroku provide postgres:// but psycopg2 needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Local SQLite fallback
    DATABASE_PATH = Path(
        os.getenv("DATABASE_PATH", "swachlens.db").replace("./", "")
    )
    if not DATABASE_PATH.is_absolute():
        DATABASE_PATH = DATA_DIR / DATABASE_PATH
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ── Authentication ────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv(
    "SECRET_KEY", "dev-secret-change-me-in-production"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "168"))  # 7 days

# ── AI / Vision ───────────────────────────────────────────────────────
AI_MODEL_PATH = Path(
    os.getenv("AI_MODEL_PATH", "").replace("./", "")
    or (BASE_DIR.parent / "ai" / "models" / "best.pt")
)
AI_MAX_PHOTO_BYTES = int(os.getenv("AI_MAX_PHOTO_BYTES", "2621440"))  # 2.5 MB

# ── CORS ──────────────────────────────────────────────────────────────
FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:8090,http://127.0.0.1:8090,http://localhost:8000,http://127.0.0.1:8000",
).split(",")
