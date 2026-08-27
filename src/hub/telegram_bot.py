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
from hub.dedupe import (
    capture_is_richer,
    collapse_user_links,
    find_link_duplicate,
    looks_like_link_capture,
    merge_capture,
)
from hub.media import save_bytes
from hub.runner import run_hub
from hub.schema import AgentTraceStep, CalendarProposal, InboxItem
from hub.store import store
from hub.tools import confirm_calendar_event, confirm_email, mark_email_preview

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hub.telegram")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("command /start from chat_id=%s", update.effective_chat.id if update.effective_chat else None)
    if update.message:
        await update.message.reply_text(
            "Hub pronto. Manda audio, foto, boleto, PDF, link ou texto. "
            "Eu organizo e proponho acoes no Calendar e no Gmail."
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
        name = message.document.file_name or f"{item.id}.bin"
        lowered = f"{name} {mime}".lower()
        if mime.startswith("audio/") or lowered.endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
            item.media_type = "audio"
        else:
            item.media_type = "document"
        path = save_bytes(f"{item.id}_{name}", media_bytes, mime)
        item.media_paths.append(path)

    if not text_bits and not media_bytes:
        await message.reply_text("Nao consegui ler esse tipo de mensagem ainda.")
        return

    merged = False
    if looks_like_link_capture(item.url, item.raw_text, item.media_type):
        collapse_user_links(user_id)
        dup = find_link_duplicate(user_id, url=item.url, text=item.raw_text)
        if dup:
            if not capture_is_richer(dup, item):
                where = dup.folder + (f"/{dup.subfolder}" if dup.subfolder else "")
                await message.reply_text(
                    f"Esse link ja estava no Hub ({where}). Nao criei outro card."
                )
                return
            item = merge_capture(dup, item)
            merged = True

    store.upsert(item)
    await message.chat.send_action("typing")
    prompt = "\n".join(text_bits) if text_bits else "(midia sem texto — interprete o arquivo anexado)"
    if merged:
        prompt = (
            "[atualizacao do mesmo post/link — enriqueça o card existente; "
            "nao trate como vaga nova]\n"
            + prompt
        )
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
        overloaded = any(
            t in str(exc)
            for t in ("503", "UNAVAILABLE", "high demand", "429", "RESOURCE_EXHAUSTED")
        )
        item = enrich(item, " ".join(text_bits))
        from hub.finance import apply_money_fallback

        item = apply_money_fallback(item, " ".join(text_bits))
        if item.media_type == "photo" and item.folder in {"Inbox", ""}:
            item.kind = "media"
            item.folder = "Fotos"
        if item.media_type == "audio" and item.folder in {"Inbox", ""}:
            item.kind = "media"
            item.folder = "Musica"
        if item.raw_text and not item.title:
            item.title = item.raw_text[:80]
        if item.media_type == "document" and item.folder == "Inbox":
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
                "O Gemini estourou a cota agora. O envio ja foi arquivado no dashboard "
                f"({item.folder}). Reenvie em ~30s para eu ler o conteudo."
            )
        elif "NOT_FOUND" in str(exc) or "404" in str(exc):
            await message.reply_text(
                "O Vertex nao achou o modelo nesta regiao. Ja tentei arquivar o que deu "
                f"(pasta {item.folder}). Se for dinheiro, olhe Finanças no dashboard."
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

    keyboard = _calendar_keyboard(item)
    await message.reply_text(reply[:4000], reply_markup=keyboard)
    await _send_cv_intent(message, item)


def _ensure_due_calendar(item: InboxItem) -> InboxItem:
    """Boleto/task with a due date always get a Calendar button, even if the LLM only asked in text."""
    if any(e.status == "proposed" for e in item.calendar):
        return item
    due = None
    title = item.summary or "Lembrete Hub"
    billed = next((f for f in item.money() if f.due_at), None)
    if billed:
        due = billed.due_at
        merchant = billed.merchant or "boleto"
        amount = billed.amount
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


def _calendar_keyboard(item: InboxItem) -> InlineKeyboardMarkup | None:
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


def _cv_intent_keyboard(item: InboxItem, email_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Sim, montar o email",
                    callback_data=f"ask:{item.id}:{email_id}",
                )
            ]
        ]
    )


def _send_keyboard(item: InboxItem, email_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Aprovar envio deste email",
                    callback_data=f"mail:{item.id}:{email_id}",
                )
            ]
        ]
    )


async def _send_cv_intent(message, item: InboxItem) -> None:
    from hub.tools import _find_cv

    for email in item.emails:
        if email.status != "proposed":
            continue
        cv_path, _cv_name = _find_cv(item.user_id)
        if cv_path:
            text = (
                "Identificamos que o post menciona um email para envio de CV "
                "e temos salvo o seu CV. Deseja enviar o seu CV?"
            )
        else:
            text = (
                "Identificamos que o post menciona um email para envio de CV, "
                "mas nao achei o arquivo do curriculo em Documentos. "
                "Arquive o PDF com titulo/tag CV e toque em montar o email mesmo assim, "
                "ou reenvie o curriculo antes."
            )
        await message.reply_text(text, reply_markup=_cv_intent_keyboard(item, email.id))
        return


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


async def on_ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    try:
        _, item_id, email_id = data.split(":", 2)
    except ValueError:
        await query.edit_message_text("Callback invalido.")
        return
    result = mark_email_preview(item_id, email_id)
    if result.get("status") != "preview":
        await query.edit_message_text(f"Nao consegui montar o email: {escape(str(result))}")
        return
    body = (result.get("body") or "").strip()
    if len(body) > 2200:
        body = body[:2200] + "\n…"
    preview = (
        "Valide o email antes do envio:\n\n"
        f"Para: {result.get('to')}\n"
        f"Assunto: {result.get('subject')}\n"
        f"Anexo: {result.get('cv_name')}\n\n"
        "Corpo:\n"
        f"{body}"
    )
    await query.edit_message_text("Ok. Segue o email formatado para voce validar.")
    item = store.get(item_id)
    if item is None or query.message is None:
        return
    await query.message.reply_text(preview[:4000], reply_markup=_send_keyboard(item, email_id))


async def on_confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    try:
        _, item_id, email_id = data.split(":", 2)
    except ValueError:
        await query.edit_message_text("Callback invalido.")
        return
    try:
        result = confirm_email(item_id, email_id)
    except Exception as exc:
        log.exception("confirm_email failed")
        await query.edit_message_text(f"Nao consegui enviar: {escape(str(exc)[:300])}")
        return
    status = result.get("status")
    if status == "sent":
        attached = "sim" if result.get("attached") else "nao"
        await query.edit_message_text(
            f"Email enviado para {result.get('to')}.\nCV anexado: {attached}"
        )
        return
    if status == "needs_gmail_oauth":
        await query.edit_message_text(
            "Falta permissao gmail.send. Rode python scripts/auth_workspace.py "
            "(aceite Gmail) e toque de novo. Calendar continua funcionando."
        )
        return
    if status == "pending_local":
        await query.edit_message_text(
            "Falta o OAuth. Rode python scripts/auth_workspace.py e toque de novo."
        )
        return
    if status == "gmail_api_disabled":
        await query.edit_message_text(
            "Gmail API ainda nao estava ligada no projeto. Ja pedi para ligar; "
            "espera um minuto e toca de novo em Aprovar envio."
        )
        return
    if status == "error":
        await query.edit_message_text(f"Nao consegui enviar: {escape(str(result.get('message') or result))}")
        return


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
    app.add_handler(CallbackQueryHandler(on_ask_email, pattern=r"^ask:"))
    app.add_handler(CallbackQueryHandler(on_confirm_email, pattern=r"^mail:"))
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
