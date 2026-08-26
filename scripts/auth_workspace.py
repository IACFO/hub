"""Interactive Google OAuth for Calendar + Drive. Run once on your machine."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hub.config import CLIENT_SECRET_PATH, TOKEN_PATH, ensure_dirs  # noqa: E402
from hub.workspace import interactive_login  # noqa: E402


def main() -> None:
    ensure_dirs()
    print(f"Client secret esperado em: {CLIENT_SECRET_PATH}")
    print("O browser vai abrir. Aceite o acesso com a conta Google do Calendar.")
    creds = interactive_login()
    print(f"Token salvo em {TOKEN_PATH}")
    print("Pronto. Reinicie o bot. Confirmacoes de evento vao para o Google Calendar.")
    if not creds.refresh_token:
        print(
            "Aviso: nao veio refresh_token. No Console, revogue o app em "
            "https://myaccount.google.com/permissions e rode este script de novo."
        )


if __name__ == "__main__":
    main()
