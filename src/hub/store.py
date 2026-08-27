from __future__ import annotations

import json
from threading import Lock
from typing import Any

from hub.config import DATA_DIR, GOOGLE_CLOUD_PROJECT, HUB_USE_FIRESTORE, ensure_dirs
from hub.schema import InboxItem, now_iso

_lock = Lock()
_ITEMS = DATA_DIR / "inbox.json"


def _load_local() -> list[dict[str, Any]]:
    ensure_dirs()
    if not _ITEMS.exists():
        return []
    return json.loads(_ITEMS.read_text(encoding="utf-8") or "[]")


def _save_local(rows: list[dict[str, Any]]) -> None:
    ensure_dirs()
    _ITEMS.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


class Store:
    def __init__(self) -> None:
        self._fs = None
        if HUB_USE_FIRESTORE:
            try:
                from google.cloud import firestore

                self._fs = firestore.Client(project=GOOGLE_CLOUD_PROJECT)
            except Exception as exc:  # noqa: BLE001
                print(f"[hub] Firestore unavailable, using local JSON: {exc}")

    def upsert(self, item: InboxItem) -> InboxItem:
        item.updated_at = now_iso()
        payload = item.model_dump()
        if self._fs is not None:
            self._fs.collection("inbox").document(item.id).set(payload)
            return item
        with _lock:
            rows = _load_local()
            rows = [r for r in rows if r.get("id") != item.id]
            rows.append(payload)
            rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
            _save_local(rows)
        return item

    def get(self, item_id: str) -> InboxItem | None:
        if self._fs is not None:
            doc = self._fs.collection("inbox").document(item_id).get()
            if not doc.exists:
                return None
            return InboxItem.model_validate(doc.to_dict())
        with _lock:
            for row in _load_local():
                if row.get("id") == item_id:
                    return InboxItem.model_validate(row)
        return None

    def list_items(self, user_id: str | None = None, limit: int = 50) -> list[InboxItem]:
        if self._fs is not None:
            query = self._fs.collection("inbox").order_by(
                "created_at", direction="DESCENDING"
            )
            if user_id:
                query = self._fs.collection("inbox").where("user_id", "==", user_id)
            docs = query.limit(limit).stream()
            return [InboxItem.model_validate(d.to_dict()) for d in docs]
        with _lock:
            rows = _load_local()
        if user_id:
            rows = [r for r in rows if r.get("user_id") == user_id]
        return [InboxItem.model_validate(r) for r in rows[:limit]]

    def search(self, query: str, user_id: str | None = None) -> list[InboxItem]:
        q = query.lower().strip()
        items = self.list_items(user_id=user_id, limit=200)
        hits = []
        for item in items:
            blob = " ".join(
                [
                    item.summary,
                    item.title,
                    item.subtitle,
                    item.body,
                    item.raw_text,
                    item.folder,
                    item.subfolder,
                    item.kind,
                    item.category,
                    item.url or "",
                    " ".join(item.tags),
                    " ".join(t.description for t in item.tasks),
                    " ".join(c.text for c in item.checklist),
                    " ".join(f"{e.to} {e.subject}" for e in item.emails),
                ]
            ).lower()
            if q in blob:
                hits.append(item)
        return hits[:30]

    def list_folders(self) -> list[str]:
        from hub.schema import FOLDERS

        names: list[str] = []
        seen: set[str] = set()
        extra = [item.folder for item in self.list_items(limit=200)]
        for name in [*FOLDERS, *extra]:
            if name and name not in seen:
                seen.add(name)
                names.append(name)
        return names


store = Store()
