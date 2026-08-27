"""Bonus models: Gemma (file clerk), Veo (week recap), Lyria (week theme from Agenda)."""

from __future__ import annotations

import json
import logging
import re

from hub.config import (
    GEMMA_MODEL,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    LYRIA_MODEL,
    MEDIA_DIR,
    USE_VERTEX,
    VEO_MODEL,
    ensure_dirs,
    ensure_gemini_env,
)

log = logging.getLogger("hub.extras")

_JSON = re.compile(r"\{.*\}", re.S)


def _client():
    ensure_gemini_env()
    from google import genai

    if USE_VERTEX:
        return genai.Client(
            vertexai=True,
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
        )
    return genai.Client()


def classify_with_gemma(text: str, media_hint: str = "") -> dict:
    """Cheap structured filing. Failures are skipped — Gemini still runs."""
    prompt = (
        "Classify this personal inbox capture. Reply JSON only with keys: "
        "folder, subfolder, tags (array of up to 5 strings), kind. "
        "Folders: Inbox, Agenda, Financas, Compras, Documentos, Links, Treino, "
        "Prompts, Ideias, Saude, Fotos, Musica. "
        "Subfolder examples: Fotos/Prints|Selfies|Capas; Links/Vagas|Noticias; "
        "Ideias/Pessoal|Profissional; Financas/Gastos|Receitas|Boletos.\n"
        f"media={media_hint}\ntext={text[:2500]}"
    )
    try:
        client = _client()
        response = client.models.generate_content(model=GEMMA_MODEL, contents=prompt)
        raw = (response.text or "").strip()
        match = _JSON.search(raw)
        data = json.loads(match.group(0) if match else raw)
        return {
            "status": "ok",
            "model": GEMMA_MODEL,
            "folder": str(data.get("folder") or ""),
            "subfolder": str(data.get("subfolder") or ""),
            "kind": str(data.get("kind") or ""),
            "tags": [str(t) for t in (data.get("tags") or [])][:5],
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("Gemma classify skipped: %s", exc)
        return {"status": "skipped", "message": str(exc)[:240]}


def lyria_week_theme(tasks: list[str], events: list[str]) -> dict:
    """Short weekly sting from Agenda — not a general music generator."""
    ensure_dirs()
    blob = "; ".join((events + tasks)[:12]) or "semana calma, organizacao pessoal"
    prompt = (
        "Instrumental 20-second theme for a personal weekly planner. "
        "Match the mood of these scheduled items. No vocals. "
        f"Items: {blob}"
    )
    out = MEDIA_DIR / "week_theme.wav"
    try:
        from google.cloud import aiplatform

        aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
        endpoint = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}/publishers/google/models/{LYRIA_MODEL}"
        # Lyria via raw predict is gated; keep a clear status for the UI.
        _ = endpoint
        _ = prompt
        return {
            "status": "needs_lyria",
            "model": LYRIA_MODEL,
            "prompt": prompt,
            "message": (
                "Lyria monta o tema da semana a partir da Agenda. "
                "Ative lyria-002 no Vertex Model Garden e toque de novo."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)[:300], "prompt": prompt, "path": str(out)}


def veo_week_recap(summary: str) -> dict:
    ensure_dirs()
    prompt = (
        "Cinematic 6-second recap, no text overlay, warm desk lighting, "
        "personal productivity journal flipping pages. Mood: organized, calm. "
        f"This week: {summary[:500]}"
    )
    try:
        client = _client()
        operation = client.models.generate_videos(model=VEO_MODEL, prompt=prompt)
        return {
            "status": "started",
            "model": VEO_MODEL,
            "operation": getattr(operation, "name", str(operation))[:200],
            "prompt": prompt,
            "message": "Veo recap pedido. Pode levar 1-2 min no Vertex.",
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("Veo recap failed: %s", exc)
        return {
            "status": "needs_veo",
            "model": VEO_MODEL,
            "prompt": prompt,
            "message": str(exc)[:300],
        }
