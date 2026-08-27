from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from telegram import Update

from hub.config import MEDIA_DIR, TELEGRAM_BOT_TOKEN, ensure_gemini_env
from hub.finance import month_summary, reports_snapshot
from hub.schema import SUBFOLDER_SEEDS
from hub.store import store

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Hub", version="0.2.0")
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


def _telegram_app():
    global _tg_app
    if _tg_app is None and TELEGRAM_BOT_TOKEN:
        from hub.telegram_bot import build_app

        _tg_app = build_app()
    return _tg_app


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
async def no_cache(request: Request, call_next):
    response: Response = await call_next(request)
    if request.url.path.startswith("/api") or request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "hub"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


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
async def api_meta() -> dict:
    return {
        "folders": store.list_folders(),
        "subfolders": SUBFOLDER_SEEDS,
        "statuses": ["inbox", "active", "done", "discarded"],
    }


@app.get("/api/inbox")
async def api_inbox(q: str | None = None) -> dict:
    if not q:
        from hub.dedupe import collapse_all_links

        collapse_all_links()
    items = store.search(q, user_id=None) if q else store.list_items(limit=200)
    return {"items": [i.model_dump() for i in items], "count": len(items)}


@app.get("/api/finance")
async def api_finance(month: str | None = None) -> dict:
    return month_summary(store.list_items(limit=500), month)


@app.get("/api/reports")
async def api_reports() -> dict:
    return reports_snapshot(store.list_items(limit=500))


@app.post("/api/reports/theme")
async def api_week_theme() -> dict:
    from hub.extras import lyria_week_theme
    from hub.finance import week_agenda

    agenda = week_agenda(store.list_items(limit=500))
    return lyria_week_theme(agenda.get("tasks") or [], agenda.get("events") or [])


@app.post("/api/reports/recap")
async def api_week_recap() -> dict:
    from hub.extras import veo_week_recap

    snap = reports_snapshot(store.list_items(limit=500))
    bits = [f"{n} em {name}" for name, n in list(snap.get("folders") or {}).items()[:6]]
    return veo_week_recap(", ".join(bits) or "semana no Hub")


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


@app.get("/api/files/{item_id}/{index}")
async def api_file(item_id: str, index: int = 0):
    item = store.get(item_id)
    if item is None or index >= len(item.media_paths):
        raise HTTPException(404, "file not found")
    raw = item.media_paths[index]
    if raw.startswith("gs://"):
        from hub.media import read_bytes

        data = read_bytes(raw)
        return Response(content=data, media_type="application/octet-stream")
    path = Path(raw).resolve()
    media_root = MEDIA_DIR.resolve()
    if not path.is_relative_to(media_root):
        raise HTTPException(403, "path denied")
    if not path.exists():
        raise HTTPException(404, "missing file")
    return FileResponse(path)


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("hub.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
