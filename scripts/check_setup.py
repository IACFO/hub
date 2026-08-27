"""Print what is configured vs what Vilson still needs to do."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hub.config import (  # noqa: E402
    CLIENT_SECRET_PATH,
    ENABLE_WORKSPACE_MCP,
    GCS_BUCKET,
    GEMINI_MODEL,
    GOOGLE_CLOUD_PROJECT,
    HUB_USE_FIRESTORE,
    TELEGRAM_BOT_TOKEN,
    TOKEN_PATH,
    USE_VERTEX,
    gemini_api_key,
)
from hub.workspace import load_user_credentials  # noqa: E402


def flag(ok: bool) -> str:
    return "OK " if ok else "FALTA"


def main() -> None:
    rows = [
        (USE_VERTEX or bool(gemini_api_key()), "Vertex AI" if USE_VERTEX else "Gemini API key (AI Studio)"),
        (bool(GEMINI_MODEL), f"Modelo {GEMINI_MODEL}"),
        (bool(TELEGRAM_BOT_TOKEN), "TELEGRAM_BOT_TOKEN (BotFather)"),
        (CLIENT_SECRET_PATH.exists(), f"OAuth desktop JSON em {CLIENT_SECRET_PATH.name}"),
        (load_user_credentials() is not None, f"Token OAuth em {TOKEN_PATH.name}"),
        (bool(GOOGLE_CLOUD_PROJECT), f"GCP project {GOOGLE_CLOUD_PROJECT}"),
        (HUB_USE_FIRESTORE, "Firestore ligado (opcional agora)"),
        (bool(GCS_BUCKET), "GCS_BUCKET (opcional agora)"),
        (ENABLE_WORKSPACE_MCP, "Workspace MCP (ligar depois do OAuth)"),
    ]
    print("Hub setup\n")
    missing = 0
    for ok, label in rows:
        print(f"  [{flag(ok)}] {label}")
        if not ok:
            missing += 1
    print()
    if not TELEGRAM_BOT_TOKEN:
        print("Proximo passo: abra o Telegram, fale com @BotFather, /newbot, cole o token no .env")
    elif load_user_credentials() is None:
        print("Proximo passo: baixe client_secret.json e rode python scripts/auth_workspace.py")
    else:
        print("Pronto para python -m hub.telegram_bot")
    sys.exit(0 if USE_VERTEX or gemini_api_key() else 1)


if __name__ == "__main__":
    main()
