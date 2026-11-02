from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

APP_NAME = "hub"
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0614591307")
USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() in {"1", "true", "yes"}
# Gemini 3.x on Vertex lives on the global endpoint, not us-central1.
GOOGLE_CLOUD_LOCATION = os.getenv(
    "GOOGLE_CLOUD_LOCATION",
    "global" if USE_VERTEX else "us-central1",
)
GCS_BUCKET = os.getenv("GCS_BUCKET", "").strip()
HUB_USE_FIRESTORE = os.getenv("HUB_USE_FIRESTORE", "false").lower() in {"1", "true", "yes"}
ENABLE_WORKSPACE_MCP = os.getenv("ENABLE_WORKSPACE_MCP", "false").lower() in {"1", "true", "yes"}
# Public demo: visitors can view inbox/reports but cannot edit, discard, or burn Gemini credits.
HUB_READ_ONLY = os.getenv("HUB_READ_ONLY", "false").lower() in {"1", "true", "yes"}
# Private dashboard. On Cloud Run, defaults to on (fail closed). Locally off unless set.
_k_service = bool(os.getenv("K_SERVICE", "").strip())
HUB_REQUIRE_AUTH = os.getenv(
    "HUB_REQUIRE_AUTH",
    "true" if _k_service else "false",
).lower() in {"1", "true", "yes"}
HUB_OWNER_EMAIL = os.getenv("HUB_OWNER_EMAIL", "vilson.dj97@gmail.com").strip().lower()
HUB_ACCESS_CODE = os.getenv("HUB_ACCESS_CODE", "").strip()
HUB_SESSION_SECRET = os.getenv("HUB_SESSION_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
DATA_DIR = Path(os.getenv("HUB_DATA_DIR", ROOT / "data"))
MEDIA_DIR = DATA_DIR / "media"
CREDENTIALS_DIR = ROOT / "credentials"
CLIENT_SECRET_PATH = CREDENTIALS_DIR / "client_secret.json"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"


def gemini_api_key() -> str:
    return (
        os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_GENAI_API_KEY", "").strip()
    )


def ensure_gemini_env() -> None:
    """ADK / google-genai: Vertex when GOOGLE_GENAI_USE_VERTEXAI=true, else AI Studio key."""
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", GOOGLE_CLOUD_LOCATION)
    if USE_VERTEX:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        return
    key = gemini_api_key()
    if key and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = key


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
