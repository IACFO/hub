from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from telegram import Update

from hub.classify import enrich
from hub.config import MEDIA_DIR, TELEGRAM_BOT_TOKEN
from hub.schema import FOLDERS
from hub.store import store

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Hub", version="0.2.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
_tg_app = None


class ItemPatch(BaseModel):
    status: str | None = None
    folder: str | None = None
    title: str | None = None
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
    for item in store.list_items(limit=500):
        store.upsert(enrich(item))


@app.middleware("http")
async def no_cache(request: Request, call_next):
    response: Response = await call_next(request)
    if request.url.path.startswith("/api") or request.url.path == "/":
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
    payload = await request.json()
    update = Update.de_json(payload, tg.bot)
    await tg.process_update(update)
    return JSONResponse({"ok": True})


@app.get("/api/meta")
async def api_meta() -> dict:
    return {"folders": FOLDERS, "statuses": ["inbox", "active", "done", "discarded"]}


@app.get("/api/inbox")
async def api_inbox(q: str | None = None) -> dict:
    items = store.search(q, user_id=None) if q else store.list_items(limit=200)
    return {"items": [i.model_dump() for i in items], "count": len(items)}


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
    path = Path(item.media_paths[index]).resolve()
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
