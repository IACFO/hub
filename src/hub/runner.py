from __future__ import annotations

import asyncio
import logging

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from hub.agent import root_agent
from hub.config import APP_NAME, ensure_gemini_env

ensure_gemini_env()
log = logging.getLogger("hub.runner")

_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)


def _is_retryable(exc: BaseException) -> bool:
    text = str(exc)
    return any(
        token in text
        for token in ("503", "UNAVAILABLE", "high demand", "RESOURCE_EXHAUSTED", "429")
    )


async def run_hub(
    user_id: str,
    text: str,
    *,
    item_id: str,
    media_bytes: bytes | None = None,
    mime_type: str | None = None,
) -> str:
    session_id = f"cap_{item_id}"
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    preamble = (
        f"[system] user_id={user_id} item_id={item_id}\n"
        "Este envio e UNICO. Ignore curriculos, CNHs ou listas de mensagens anteriores.\n"
        "Use exatamente esses ids nas tools.\n\n"
        f"{text}"
    )
    parts: list[types.Part] = [types.Part(text=preamble)]
    if media_bytes and mime_type:
        parts.append(types.Part.from_bytes(data=media_bytes, mime_type=mime_type))

    last_error: BaseException | None = None
    for attempt in range(3):
        try:
            return await _collect_reply(user_id, session_id, parts)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < 2 and _is_retryable(exc):
                wait = 2 ** attempt
                log.warning("Gemini retry %s after %ss: %s", attempt + 1, wait, exc)
                await asyncio.sleep(wait)
                continue
            raise
    raise last_error or RuntimeError("agent failed")


async def _collect_reply(user_id: str, session_id: str, parts: list[types.Part]) -> str:
    final = "Nao consegui processar este envio."
    async for event in _runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=parts),
    ):
        if event.content and event.content.parts:
            texts = [p.text for p in event.content.parts if getattr(p, "text", None)]
            if texts and not getattr(event, "partial", False):
                final = "\n".join(texts)
    return final.strip()
