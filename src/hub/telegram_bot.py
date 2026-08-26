from __future__ import annotations

import logging
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from hub.classify import enrich, extract_url
from hub.config import TELEGRAM_BOT_TOKEN, ensure_dirs, ensure_gemini_env
from hub.media import save_bytes
from hub.runner import run_hub
from hub.schema import AgentTraceStep, CalendarProposal, InboxItem
from hub.store import store
from hub.tools import confirm_calendar_event

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hub.telegram")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("command /start from chat_id=%s", update.effective_chat.id if update.effective_chat else None)
    if update.message:
        await update.message.reply_text(
            "Hub pronto. Manda audio, foto, boleto, PDF, link ou texto. "
            "Eu organizo e proponho acoes no Calendar."
        )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("unknown command: %s", update.effective_message.text if update.effective_message else None)
    if update.message:
        await update.message.reply_text(
            "Comando desconhecido. Envie /start (com t no final) ou uma mensagem, audio ou foto."
        )


async def handle_capture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    log.info(
        "capture chat_id=%s user=%s text=%s",
        message.chat_id if message else None,
        user.id if user else None,
        (message.text or message.caption or getattr(message, "content_type", None)) if message else None,
    )
    if message is None or user is None:
        return

    user_id = str(user.id)
    item = InboxItem(user_id=user_id, telegram_chat_id=message.chat_id, telegram_message_id=message.message_id)
    media_bytes: bytes | None = None
    mime: str | None = None
    text_bits: list[str] = []

    if message.text:
        text_bits.append(message.text)
        item.media_type = "link" if message.text.strip().startswith("http") else "text"
        item.raw_text = message.text
    if message.caption:
        text_bits.append(message.caption)
        item.raw_text = (item.raw_text + " " + message.caption).strip()

    for entity_source, entity_text in (
        (getattr(message, "entities", None), message.text),
        (getattr(message, "caption_entities", None), message.caption),
    ):
        if entity_source and entity_text:
            for entity in entity_source:
                if entity.type == "url":
                    item.url = entity_text[entity.offset : entity.offset + entity.length]
                elif entity.type == "text_link" and entity.url:
                    item.url = entity.url
    if not item.url:
        item.url = extract_url(item.raw_text)

    if message.voice:
        file = await message.voice.get_file()
        media_bytes = bytes(await file.download_as_bytearray())
        mime = "audio/ogg"
        item.media_type = "voice"
        path = save_bytes(f"{item.id}.ogg", media_bytes, mime)
        item.media_paths.append(path)
    elif message.audio:
        file = await message.audio.get_file()
        media_bytes = bytes(await file.download_as_bytearray())
        mime = message.audio.mime_type or "audio/mpeg"
        item.media_type = "audio"
        path = save_bytes(f"{item.id}.audio", media_bytes, mime)
        item.media_paths.append(path)
    elif message.photo:
        file = await message.photo[-1].get_file()
        media_bytes = bytes(await file.download_as_bytearray())
        mime = "image/jpeg"
        item.media_type = "photo"
        path = save_bytes(f"{item.id}.jpg", media_bytes, mime)
        item.media_paths.append(path)
    elif message.document:
        file = await message.document.get_file()
        media_bytes = bytes(await file.download_as_bytearray())
        mime = message.document.mime_type or "application/octet-stream"
        item.media_type = "document"
        name = message.document.file_name or f"{item.id}.bin"
        path = save_bytes(f"{item.id}_{name}", media_bytes, mime)
        item.media_paths.append(path)

    if not text_bits and not media_bytes:
        await message.reply_text("Nao consegui ler esse tipo de mensagem ainda.")
        return

    store.upsert(item)
    await message.chat.send_action("typing")
    prompt = "\n".join(text_bits) if text_bits else "(midia sem texto — interprete o arquivo anexado)"
    try:
        reply = await run_hub(
            user_id,
            prompt,
            item_id=item.id,
            media_bytes=media_bytes,
            mime_type=mime,
        )
    except Exception as exc:
        log.exception("agent run failed")
        item = store.get(item.id) or item
        overloaded = any(t in str(exc) for t in ("503", "UNAVAILABLE", "high demand"))
        if item.media_type == "document":
            from pathlib import Path

            item.kind = "document"
            item.folder = "Documentos"
            item.category = "documentos"
            if item.media_paths and not item.title:
                item.title = Path(item.media_paths[0]).name
            item.summary = item.summary or "Arquivo salvo. Leitura da IA pendente."
            store.upsert(item)
        if overloaded:
            await message.reply_text(
                "O Gemini estava sobrecarregado (503), nao e um arquivo corrompido. "
                "O PDF ja ficou em Documentos no dashboard. Reenvie em 20s para eu ler o conteudo."
            )
        else:
            await message.reply_text("Falha ao processar. Tenta de novo em alguns segundos.")
        return

    item = store.get(item.id) or item
    item.agent_reply = reply
    item.trace.append(AgentTraceStep(kind="agent_reply", detail=reply[:500]))
    item = enrich(item, " ".join(text_bits))
    item = _ensure_due_calendar(item)
    store.upsert(item)

    keyboard = _confirmation_keyboard(item)
    await message.reply_text(reply[:4000], reply_markup=keyboard)


def _ensure_due_calendar(item: InboxItem) -> InboxItem:
    """Boleto/task with a due date always get a Calendar button, even if the LLM only asked in text."""
    if any(e.status == "proposed" for e in item.calendar):
        return item
    due = None
    title = item.summary or "Lembrete Hub"
    if item.financial and item.financial.due_at:
        due = item.financial.due_at
        merchant = item.financial.merchant or "boleto"
        amount = item.financial.amount
        title = f"Pagar {merchant}"
        if amount is not None:
            title += f" (R$ {amount:.2f})"
    else:
        for task in item.tasks:
            if task.due_at:
                due = task.due_at
                title = task.description
                break
    if not due:
        return item
    start = due if "T" in due else f"{due}T09:00:00-03:00"
    item.calendar.append(
        CalendarProposal(title=title[:80], start=start, description=item.summary)
    )
    item.trace.append(AgentTraceStep(kind="auto_calendar", detail=f"{title} @ {start}"))
    return item


def _confirmation_keyboard(item: InboxItem) -> InlineKeyboardMarkup | None:
    rows = []
    for event in item.calendar:
        if event.status == "proposed":
            rows.append(
                [
                    InlineKeyboardButton(
                        f"Confirmar: {event.title[:42]}",
                        callback_data=f"cal:{item.id}:{event.id}",
                    )
                ]
            )
    if not rows:
        return None
    return InlineKeyboardMarkup(rows)


async def on_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    try:
        _, item_id, event_id = data.split(":", 2)
    except ValueError:
        await query.edit_message_text("Callback invalido.")
        return
    result = confirm_calendar_event(item_id, event_id)
    if result.get("status") == "created":
        item = store.get(item_id)
        drive_bits = []
        if item:
            from hub.tools import attach_media_to_drive

            for path in item.media_paths:
                uploaded = attach_media_to_drive(item_id, path)
                if uploaded.get("link"):
                    drive_bits.append(uploaded["link"])
        link = result.get("html_link") or ""
        extra = ("\nDrive: " + " ".join(drive_bits)) if drive_bits else ""
        await query.edit_message_text(f"Evento criado no Google Calendar.\n{link}{extra}")
        return
    if result.get("status") == "pending_local":
        await query.edit_message_text(
            "Acao confirmada no Hub. Falta o OAuth do Calendar — "
            "rode python scripts/auth_workspace.py e confirme de novo."
        )
        return
    await query.edit_message_text(f"Nao consegui criar o evento: {escape(str(result))}")


def build_app() -> Application:
    ensure_gemini_env()
    ensure_dirs()
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN vazio. Crie o bot no @BotFather e cole o token no .env."
        )
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_confirm, pattern=r"^cal:"))
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.VOICE | filters.AUDIO | filters.PHOTO | filters.Document.ALL)
            & ~filters.COMMAND,
            handle_capture,
        )
    )
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    return app


def main() -> None:
    log.info("Hub Telegram bot starting (polling)")
    build_app().run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
