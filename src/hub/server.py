from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from telegram import Update

from hub.auth import (
    auth_enabled,
    auth_ready,
    check_access_code,
    clear_cookie,
    is_public_path,
    login_redirect,
    read_login_code,
    record_failure,
    session_email,
    too_many_failures,
)
from hub.config import (
    HUB_OWNER_EMAIL,
    HUB_READ_ONLY,
    MEDIA_DIR,
    TELEGRAM_BOT_TOKEN,
    ensure_gemini_env,
)
from hub.finance import add_months, finance_report, list_payables, month_summary, reports_snapshot
from hub.media import delete_path, save_bytes
from hub.schema import FINANCE_CATEGORIES, FinancialFact, InboxItem
from hub.store import store

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Hub", version="0.3.1")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
_tg_app = None


class ItemPatch(BaseModel):
    status: str | None = None
    folder: str | None = None
    subfolder: str | None = None
    title: str | None = None
    subtitle: str | None = None
    summary: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    kind: str | None = None


class CheckPatch(BaseModel):
    checked: bool


class FolderCreate(BaseModel):
    name: str
    folder: str | None = None
    subfolder: str | None = None


class FinanceEntry(BaseModel):
    amount: float
    kind: str = "gasto"
    category: str = "outros"
    merchant: str | None = None
    occurred_at: str | None = None
    month: str | None = None


class FinanceCategoryBody(BaseModel):
    name: str
    id: str | None = None
    month: str | None = None


class FinanceTypeBody(BaseModel):
    name: str
    id: str | None = None
    side: str | None = None
    month: str | None = None


class PayableBody(BaseModel):
    amount: float
    description: str = ""
    category: str = "outros"
    due_at: str | None = None
    paid_at: str | None = None
    status: str = "aberto"
    recurring_months: int = 1
    month: str | None = None


class AccountingMonthBody(BaseModel):
    month: str | None = None
    revenue: float = 0
    distribution: float = 0


class AccountingExpenseBody(BaseModel):
    month: str | None = None
    id: str | None = None
    description: str = ""
    amount: float = 0


def _telegram_app():
    global _tg_app
    if _tg_app is None and TELEGRAM_BOT_TOKEN:
        from hub.telegram_bot import build_app

        _tg_app = build_app()
    return _tg_app


def _read_only_error() -> JSONResponse:
    return JSONResponse(
        {
            "error": "read_only",
            "message": "Public demo is read-only. Editing and generation are disabled.",
        },
        status_code=403,
    )


@app.on_event("startup")
async def _startup() -> None:
    ensure_gemini_env()


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _tg_app
    if _tg_app is not None and _tg_app.running:
        await _tg_app.stop()
        await _tg_app.shutdown()
        _tg_app = None


@app.middleware("http")
async def security_and_cache(request: Request, call_next):
    path = request.url.path
    method = request.method.upper()

    if auth_enabled() and not is_public_path(path):
        if not auth_ready():
            return JSONResponse(
                {"error": "auth_not_configured", "message": "Private access is not configured."},
                status_code=503,
            )
        if session_email(request) is None:
            if path.startswith("/api"):
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            return RedirectResponse("/login", status_code=303)

    # Public demo: block mutations. Telegram webhook stays open for the owner bot.
    if HUB_READ_ONLY and method in {"POST", "PUT", "PATCH", "DELETE"}:
        if path != "/telegram/webhook":
            return _read_only_error()

    response: Response = await call_next(request)
    if path.startswith("/api") or path == "/" or path.startswith("/static/") or path in {"/login"}:
        response.headers["Cache-Control"] = "no-store, max-age=0"
    if HUB_READ_ONLY:
        response.headers["X-Hub-Read-Only"] = "1"
    return response


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "hub", "read_only": HUB_READ_ONLY}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/login")
async def login_page(request: Request):
    if auth_enabled() and session_email(request):
        return RedirectResponse("/", status_code=303)
    return FileResponse(STATIC / "login.html")


@app.post("/auth/login")
async def auth_login(request: Request):
    if not auth_enabled():
        return RedirectResponse("/", status_code=303)
    if not auth_ready():
        return JSONResponse({"error": "auth_not_configured"}, status_code=503)
    if too_many_failures(request):
        return RedirectResponse("/login?e=1", status_code=303)
    code = await read_login_code(request)
    if not check_access_code(code):
        record_failure(request)
        return RedirectResponse("/login?e=1", status_code=303)
    return login_redirect(HUB_OWNER_EMAIL)


@app.post("/auth/logout")
async def auth_logout():
    response = RedirectResponse("/login", status_code=303)
    clear_cookie(response)
    return response


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    tg = _telegram_app()
    if tg is None:
        return JSONResponse({"error": "bot token missing"}, status_code=503)
    if not tg.running:
        await tg.initialize()
        await tg.start()
    payload = await request.json()
    update = Update.de_json(payload, tg.bot)
    await tg.process_update(update)
    return JSONResponse({"ok": True})


@app.get("/api/meta")
async def api_meta(request: Request) -> dict:
    return {
        "folders": store.list_folders(),
        "subfolders": store.list_subfolders(),
        "statuses": ["inbox", "active", "done"],
        "read_only": HUB_READ_ONLY,
        "auth": auth_enabled(),
        "email": session_email(request) or "",
    }


@app.get("/api/inbox")
async def api_inbox(q: str | None = None) -> dict:
    # collapse_all_links mutates store — skip in public demo
    if not q and not HUB_READ_ONLY:
        from hub.dedupe import collapse_all_links

        collapse_all_links()
    items = store.search(q, user_id=None) if q else store.list_items(limit=200)
    return {"items": [i.model_dump() for i in items], "count": len(items)}


@app.get("/api/finance")
async def api_finance(month: str | None = None) -> dict:
    return _finance_snapshot(month)


@app.get("/api/reports")
async def api_reports() -> dict:
    return reports_snapshot(store.list_items(limit=500))


@app.post("/api/folders")
async def api_create_folder(body: FolderCreate) -> dict:
    try:
        name = store.add_folder(body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "name": name, **store.snapshot()}


@app.patch("/api/folders")
async def api_rename_folder(body: FolderCreate) -> dict:
    try:
        name = store.rename_folder(body.folder or "", body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "name": name, **store.snapshot()}


@app.delete("/api/folders")
async def api_delete_folder(name: str) -> dict:
    try:
        store.delete_folder(name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, **store.snapshot()}


@app.post("/api/folders/subfolders")
async def api_create_subfolder(body: FolderCreate) -> dict:
    try:
        name = store.add_subfolder(body.folder or "", body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "name": name, "folder": body.folder, **store.snapshot()}


@app.patch("/api/folders/subfolders")
async def api_rename_subfolder(body: FolderCreate) -> dict:
    try:
        name = store.rename_subfolder(body.folder or "", body.subfolder or "", body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "name": name, "folder": body.folder, **store.snapshot()}


@app.delete("/api/folders/subfolders")
async def api_delete_subfolder(folder: str, name: str) -> dict:
    try:
        store.delete_subfolder(folder, name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, **store.snapshot()}


@app.post("/api/uploads")
async def api_upload(request: Request) -> dict:
    form = await request.form()
    folder = str(form.get("folder") or "").strip()
    subfolder = str(form.get("subfolder") or "").strip()
    files = form.getlist("files")
    if not files:
        raise HTTPException(400, "No files uploaded")
    created = []
    for upload in files:
        if not hasattr(upload, "read"):
            continue
        filename = getattr(upload, "filename", None) or "file"
        data = await upload.read()
        if not data:
            continue
        if len(data) > 25 * 1024 * 1024:
            raise HTTPException(413, f"{filename} is larger than 25MB")
        created.append(_item_from_upload(filename, data, getattr(upload, "content_type", None), folder, subfolder))
    if not created:
        raise HTTPException(400, "No readable files")
    return {"ok": True, "count": len(created), "items": [item.model_dump() for item in created]}


@app.patch("/api/items/{item_id}")
async def api_patch_item(item_id: str, patch: ItemPatch) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    data = patch.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(item, key, value)
    store.upsert(item)
    return item.model_dump()


@app.delete("/api/items/{item_id}")
async def api_delete_item(item_id: str) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    for path in item.media_paths:
        delete_path(path)
    store.delete(item_id)
    return {"ok": True, "id": item_id}


@app.delete("/api/files/{item_id}/{index}")
async def api_delete_file(item_id: str, index: int) -> dict:
    item = store.get(item_id)
    if item is None or index < 0 or index >= len(item.media_paths):
        raise HTTPException(404, "file not found")
    path = item.media_paths.pop(index)
    delete_path(path)
    store.upsert(item)
    return item.model_dump()


def _type_sides() -> dict[str, str]:
    return {row["id"]: row.get("side") or "saida" for row in store.list_finance_types()}


def _finance_kind(kind: str) -> str:
    raw = (kind or "").strip().lower()
    known = set(_type_sides())
    if raw in known:
        return raw
    from hub.store import _slug_category

    slug = _slug_category(raw)
    if slug in known:
        return slug
    return "gasto"


def _ledger_subfolder(kind: str) -> str:
    if kind == "boleto":
        return "Boletos"
    if _type_sides().get(kind) == "entrada" or kind == "receita":
        return "Receitas"
    return "Gastos"


def _bill_status(value: str) -> str:
    text = (value or "").strip().lower()
    if text in {"pago", "paid", "quitado"}:
        return "pago"
    if text in {"cancelado", "cancelled", "canceled"}:
        return "cancelado"
    return "aberto"


def _paid_date(status: str, paid_at: str | None, due: str | None) -> str | None:
    if status != "pago":
        return None
    raw = (paid_at or "")[:10]
    if len(raw) >= 10 and raw[4] == "-":
        return raw
    if due and len(due) >= 10:
        return due[:10]
    from datetime import datetime, timedelta, timezone

    return datetime.now(timezone(timedelta(hours=-3))).strftime("%Y-%m-%d")


def _new_payable(description: str, amount: float, category: str, due: str | None, status: str, paid_at: str | None) -> None:
    item = InboxItem(
        user_id=HUB_OWNER_EMAIL or "owner",
        source="web",
        kind="finance",
        status="active",
        folder="Financas",
        subfolder="Contas",
        category="financas",
        title=description,
        media_type="text",
        tags=["payable"],
    )
    fact = FinancialFact(
        amount=amount,
        kind="boleto",
        category=category,
        merchant=description,
        due_at=due,
        occurred_at=due,
        bill_status=status,
        paid_at=paid_at,
    )
    item.financials = [fact]
    item.financial = fact
    store.upsert(item)


def _finance_category(kind: str, category: str) -> str:
    raw = (category or "").strip()
    cat = raw.lower()
    known = {row["id"] for row in store.list_finance_categories()}
    known.update(FINANCE_CATEGORIES)
    if cat in known:
        return cat
    from hub.store import _slug_category

    slug = _slug_category(raw)
    if slug in known:
        return slug
    if _type_sides().get(kind) == "entrada" or kind == "receita":
        return "renda"
    return "outros"


def _finance_snapshot(month: str | None = None) -> dict:
    items = store.list_items(limit=500)
    sides = _type_sides()
    data = month_summary(items, month, sides)
    data["categories"] = store.list_finance_categories()
    data["types"] = store.list_finance_types()
    data["payables"] = list_payables(items)
    data["report"] = finance_report(items, data["month"], sides)
    return data


@app.post("/api/finance/categories")
async def api_finance_create_category(body: FinanceCategoryBody) -> dict:
    try:
        row = store.add_finance_category(body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "category": row, **_finance_snapshot(body.month)}


@app.patch("/api/finance/categories")
async def api_finance_rename_category(body: FinanceCategoryBody) -> dict:
    try:
        row = store.rename_finance_category(body.id or "", body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "category": row, **_finance_snapshot(body.month)}


@app.delete("/api/finance/categories")
async def api_finance_delete_category(id: str, month: str | None = None) -> dict:
    try:
        store.delete_finance_category(id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, **_finance_snapshot(month)}


@app.post("/api/finance/types")
async def api_finance_create_type(body: FinanceTypeBody) -> dict:
    try:
        row = store.add_finance_type(body.name, body.side or "saida")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "type": row, **_finance_snapshot(body.month)}


@app.patch("/api/finance/types")
async def api_finance_rename_type(body: FinanceTypeBody) -> dict:
    try:
        row = store.rename_finance_type(body.id or "", body.name, body.side)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "type": row, **_finance_snapshot(body.month)}


@app.delete("/api/finance/types")
async def api_finance_delete_type(id: str, month: str | None = None) -> dict:
    try:
        store.delete_finance_type(id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, **_finance_snapshot(month)}


@app.post("/api/finance/payables")
async def api_payable_create(body: PayableBody) -> dict:
    status = _bill_status(body.status)
    cat = _finance_category("boleto", body.category)
    when = (body.due_at or "")[:10] or None
    description = (body.description or "").strip() or "Conta"
    copies = max(1, min(int(body.recurring_months or 1), 36))
    for offset in range(copies):
        due = add_months(when, offset) if when else None
        this_status = status if offset == 0 else "aberto"
        _new_payable(
            description,
            float(body.amount),
            cat,
            due,
            this_status,
            _paid_date(this_status, body.paid_at, due),
        )
    return {"ok": True, "count": copies, **_finance_snapshot(body.month)}


@app.patch("/api/finance/payables/{item_id}/{fact_id}")
async def api_payable_update(item_id: str, fact_id: str, body: PayableBody) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    status = _bill_status(body.status)
    cat = _finance_category("boleto", body.category)
    found = None
    for fact in item.financials:
        if fact.id == fact_id and (fact.bill_status or "").strip():
            fact.amount = float(body.amount)
            fact.category = cat
            fact.merchant = (body.description or "").strip() or fact.merchant
            fact.due_at = (body.due_at or "")[:10] or fact.due_at
            fact.occurred_at = fact.due_at
            fact.bill_status = status
            fact.paid_at = _paid_date(status, body.paid_at, fact.due_at)
            found = fact
            break
    if found is None:
        raise HTTPException(404, "bill not found")
    item.financial = item.financials[0]
    item.title = found.merchant or item.title
    item.subfolder = "Contas"
    store.upsert(item)
    return {"ok": True, "item": item.model_dump(), **_finance_snapshot(body.month)}


@app.delete("/api/finance/payables/{item_id}/{fact_id}")
async def api_payable_delete(item_id: str, fact_id: str, month: str | None = None) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    before = len(item.financials)
    item.financials = [
        fact for fact in item.financials if not (fact.id == fact_id and (fact.bill_status or "").strip())
    ]
    if len(item.financials) == before:
        raise HTTPException(404, "bill not found")
    if not item.financials:
        store.delete(item_id)
    else:
        item.financial = item.financials[0]
        store.upsert(item)
    return {"ok": True, **_finance_snapshot(month)}


@app.post("/api/finance/entries")
async def api_finance_create(body: FinanceEntry) -> dict:
    kind = _finance_kind(body.kind)
    cat = _finance_category(kind, body.category)
    when = (body.occurred_at or "")[:10] or None
    merchant = (body.merchant or "").strip() or "Lançamento"
    item = InboxItem(
        user_id=HUB_OWNER_EMAIL or "owner",
        source="web",
        kind="finance",
        status="active",
        folder="Financas",
        subfolder=_ledger_subfolder(kind),
        category="financas",
        title=merchant,
        media_type="text",
    )
    fact = FinancialFact(
        amount=float(body.amount),
        kind=kind,
        category=cat,
        merchant=merchant,
        occurred_at=when,
    )
    item.financials = [fact]
    item.financial = fact
    store.upsert(item)
    return {"ok": True, "item": item.model_dump(), **_finance_snapshot(body.month)}


@app.patch("/api/finance/entries/{item_id}/{fact_id}")
async def api_finance_update(item_id: str, fact_id: str, body: FinanceEntry) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    kind = _finance_kind(body.kind)
    cat = _finance_category(kind, body.category)
    found = None
    for fact in item.financials:
        if fact.id == fact_id:
            fact.amount = float(body.amount)
            fact.kind = kind
            fact.category = cat
            fact.merchant = (body.merchant or "").strip() or fact.merchant
            fact.occurred_at = (body.occurred_at or "")[:10] or fact.occurred_at
            found = fact
            break
    if found is None:
        raise HTTPException(404, "entry not found")
    item.financial = item.financials[0]
    if item.kind == "finance":
        item.title = found.merchant or item.title
        item.subfolder = _ledger_subfolder(kind)
    store.upsert(item)
    return {"ok": True, "item": item.model_dump(), **_finance_snapshot(body.month)}


@app.delete("/api/finance/entries/{item_id}/{fact_id}")
async def api_finance_delete(item_id: str, fact_id: str, month: str | None = None) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    before = len(item.financials)
    item.financials = [fact for fact in item.financials if fact.id != fact_id]
    if len(item.financials) == before:
        raise HTTPException(404, "entry not found")
    if not item.financials:
        store.delete(item_id)
    else:
        item.financial = item.financials[0]
        store.upsert(item)
    return {"ok": True, **_finance_snapshot(month)}


@app.get("/api/accounting")
async def api_accounting(month: str | None = None) -> dict:
    return store.accounting_view(month)


@app.put("/api/accounting")
async def api_accounting_save(body: AccountingMonthBody) -> dict:
    try:
        return store.save_accounting_month(body.month, body.revenue, body.distribution)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/accounting/expenses")
async def api_accounting_add_expense(body: AccountingExpenseBody) -> dict:
    try:
        return store.add_accounting_expense(body.month, body.description, body.amount)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.patch("/api/accounting/expenses")
async def api_accounting_update_expense(body: AccountingExpenseBody) -> dict:
    if not body.id:
        raise HTTPException(400, "expense not found")
    try:
        return store.update_accounting_expense(body.month, body.id, body.description, body.amount)
    except ValueError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status, str(exc)) from exc


@app.delete("/api/accounting/expenses")
async def api_accounting_delete_expense(month: str | None = None, expense_id: str | None = None) -> dict:
    if not expense_id:
        raise HTTPException(400, "expense not found")
    try:
        return store.delete_accounting_expense(month, expense_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.patch("/api/items/{item_id}/check/{check_id}")
async def api_patch_check(item_id: str, check_id: str, patch: CheckPatch) -> dict:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(404, "not found")
    for row in item.checklist:
        if row.id == check_id:
            row.checked = patch.checked
            store.upsert(item)
            return item.model_dump()
    raise HTTPException(404, "check not found")


def _item_from_upload(filename: str, data: bytes, content_type: str | None, folder: str, subfolder: str):
    from hub.classify import enrich

    safe_name = Path(filename).name or "file"
    mime = (content_type or _guess_media_type(safe_name)).split(";")[0].strip()
    item = InboxItem(user_id=HUB_OWNER_EMAIL or "owner", source="web")
    stored = save_bytes(f"{item.id}_{safe_name}", data, mime or "application/octet-stream")
    item.media_paths.append(stored)
    item.title = Path(safe_name).stem.replace("_", " ").strip() or safe_name
    item.raw_text = safe_name
    lowered = f"{safe_name} {mime}".lower()
    if mime.startswith("image/"):
        item.media_type = "photo"
        item.kind = "media"
    elif mime.startswith("audio/") or lowered.endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
        item.media_type = "audio"
        item.kind = "media"
    else:
        item.media_type = "document"
        item.kind = "document"
    if folder and folder.lower() not in {"tudo", "all", ""}:
        item.folder = folder
    if subfolder:
        item.subfolder = subfolder
    item = enrich(item, safe_name)
    if folder and folder.lower() not in {"tudo", "all", ""}:
        item.folder = folder
    if subfolder:
        item.subfolder = subfolder
    return store.upsert(item)


def _guess_media_type(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".mp3"):
        return "audio/mpeg"
    if lower.endswith(".wav"):
        return "audio/wav"
    if lower.endswith(".ogg"):
        return "audio/ogg"
    if lower.endswith((".m4a", ".mp4")):
        return "audio/mp4"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    return "application/octet-stream"


def _download_name(raw: str, item_id: str, index: int) -> str:
    base = Path(raw.replace("gs://", "")).name or f"{item_id}-{index}"
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in base)
    return safe or f"{item_id}-{index}.bin"


@app.get("/api/files/{item_id}/{index}")
async def api_file(item_id: str, index: int = 0, download: bool = False):
    item = store.get(item_id)
    if item is None or index >= len(item.media_paths):
        raise HTTPException(404, "file not found")
    raw = item.media_paths[index]
    filename = _download_name(raw, item_id, index)
    media_type = _guess_media_type(filename)
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    if raw.startswith("gs://"):
        from hub.media import read_bytes

        data = read_bytes(raw)
        return Response(content=data, media_type=media_type, headers=headers)
    path = Path(raw).resolve()
    media_root = MEDIA_DIR.resolve()
    if not path.is_relative_to(media_root):
        raise HTTPException(403, "path denied")
    if not path.exists():
        raise HTTPException(404, "missing file")
    if download:
        return FileResponse(path, media_type=media_type, filename=filename)
    return FileResponse(path, media_type=media_type)


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("hub.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
