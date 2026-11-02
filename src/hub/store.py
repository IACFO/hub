from __future__ import annotations

import json
import re
import time
import unicodedata
from threading import Lock
from typing import Any

from hub.config import DATA_DIR, GOOGLE_CLOUD_PROJECT, HUB_USE_FIRESTORE, ensure_dirs
from hub.accounting import (
    clean_description,
    compute,
    normalize_month,
    order_months,
    parse_money,
)
from hub.schema import FINANCE_CATEGORIES, FINANCE_TYPES, FOLDERS, SUBFOLDER_SEEDS, InboxItem, new_id, now_iso

_TAXONOMY = DATA_DIR / "taxonomy.json"
_ACCOUNTING = DATA_DIR / "accounting.json"
_RESERVED_FOLDERS = {"", "tudo", "all", "todas"}
_PROTECTED_FOLDERS = {"inbox"}

_lock = Lock()
_ITEMS = DATA_DIR / "inbox.json"
_SYNC_SECONDS = 30
_FULL_RELOAD_SECONDS = 900


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
        # Firestore read cache. Reading the whole inbox on every dashboard poll blew past
        # the 50k free reads/day. Now: full load per cold start, then every 30s only docs
        # whose updated_at moved (other Cloud Run instances), full reload every 15 min
        # to drop deletes made elsewhere.
        self._rows: dict[str, dict[str, Any]] | None = None
        self._rows_full_at = 0.0
        self._rows_synced_at = 0.0
        self._rows_watermark = ""
        self._meta: dict[str, tuple[float, dict[str, Any]]] = {}
        self._fs_lock = Lock()
        if HUB_USE_FIRESTORE:
            try:
                from google.cloud import firestore

                self._fs = firestore.Client(project=GOOGLE_CLOUD_PROJECT)
            except Exception as exc:  # noqa: BLE001
                print(f"[hub] Firestore unavailable, using local JSON: {exc}")

    def _fs_rows(self) -> dict[str, dict[str, Any]]:
        with self._fs_lock:
            now = time.monotonic()
            col = self._fs.collection("inbox")
            if self._rows is None or now - self._rows_full_at > _FULL_RELOAD_SECONDS:
                self._rows = {doc.id: doc.to_dict() or {} for doc in col.stream()}
                self._rows_full_at = self._rows_synced_at = now
                self._rows_watermark = max(
                    (r.get("updated_at") or "" for r in self._rows.values()), default=""
                )
            elif now - self._rows_synced_at > _SYNC_SECONDS:
                for doc in col.where("updated_at", ">=", self._rows_watermark).stream():
                    row = doc.to_dict() or {}
                    self._rows[doc.id] = row
                    self._rows_watermark = max(self._rows_watermark, row.get("updated_at") or "")
                self._rows_synced_at = now
            return self._rows

    def _fs_meta(self, name: str) -> dict[str, Any]:
        with self._fs_lock:
            now = time.monotonic()
            cached = self._meta.get(name)
            if cached is None or now - cached[0] > _SYNC_SECONDS:
                doc = self._fs.collection("hub_meta").document(name).get()
                cached = (now, (doc.to_dict() or {}) if doc.exists else {})
                self._meta[name] = cached
            return cached[1]

    def _fs_set_meta(self, name: str, payload: dict[str, Any]) -> None:
        self._fs.collection("hub_meta").document(name).set(payload)
        with self._fs_lock:
            self._meta[name] = (time.monotonic(), payload)

    def upsert(self, item: InboxItem) -> InboxItem:
        item.updated_at = now_iso()
        payload = item.model_dump()
        if self._fs is not None:
            self._fs.collection("inbox").document(item.id).set(payload)
            rows = self._fs_rows()
            with self._fs_lock:
                rows[item.id] = payload
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
            row = self._fs_rows().get(item_id)
            return InboxItem.model_validate(row) if row else None
        with _lock:
            for row in _load_local():
                if row.get("id") == item_id:
                    return InboxItem.model_validate(row)
        return None

    def delete(self, item_id: str) -> bool:
        if self.get(item_id) is None:
            return False
        if self._fs is not None:
            self._fs.collection("inbox").document(item_id).delete()
            rows = self._fs_rows()
            with self._fs_lock:
                rows.pop(item_id, None)
            return True
        with _lock:
            rows = [row for row in _load_local() if row.get("id") != item_id]
            _save_local(rows)
        return True

    def list_items(self, user_id: str | None = None, limit: int = 50) -> list[InboxItem]:
        if self._fs is not None:
            cached = self._fs_rows()
            with self._fs_lock:
                rows = sorted(cached.values(), key=lambda r: r.get("created_at", ""), reverse=True)
        else:
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

    def _load_taxonomy(self) -> dict[str, Any]:
        empty = {
            "folders": [],
            "subfolders": {},
            "hidden_folders": [],
            "hidden_subfolders": {},
            "finance_categories": [],
            "hidden_finance_categories": [],
            "finance_types": [],
            "hidden_finance_types": [],
        }
        raw: dict[str, Any] = {}
        if self._fs is not None:
            raw = self._fs_meta("taxonomy")
        else:
            ensure_dirs()
            if _TAXONOMY.exists():
                try:
                    raw = json.loads(_TAXONOMY.read_text(encoding="utf-8") or "{}")
                except json.JSONDecodeError:
                    raw = {}
        if not raw:
            return empty
        hidden_subs = raw.get("hidden_subfolders") or {}
        if not isinstance(hidden_subs, dict):
            hidden_subs = {}
        finance_cats = []
        for row in raw.get("finance_categories") or []:
            if isinstance(row, dict) and row.get("id"):
                finance_cats.append(
                    {"id": str(row["id"]), "label": str(row.get("label") or "").strip()}
                )
            elif isinstance(row, str) and row.strip():
                slug = _slug_category(row)
                if slug:
                    finance_cats.append({"id": slug, "label": row.strip()})
        return {
            "folders": list(raw.get("folders") or []),
            "subfolders": dict(raw.get("subfolders") or {}),
            "hidden_folders": list(raw.get("hidden_folders") or []),
            "hidden_subfolders": {str(k): list(v or []) for k, v in hidden_subs.items()},
            "finance_categories": finance_cats,
            "hidden_finance_categories": list(raw.get("hidden_finance_categories") or []),
            "finance_types": _parse_finance_types(raw.get("finance_types")),
            "hidden_finance_types": list(raw.get("hidden_finance_types") or []),
        }

    def _save_taxonomy(self, data: dict[str, Any]) -> None:
        hidden_subs = data.get("hidden_subfolders") or {}
        payload = {
            "folders": list(data.get("folders") or []),
            "subfolders": dict(data.get("subfolders") or {}),
            "hidden_folders": list(data.get("hidden_folders") or []),
            "hidden_subfolders": {str(k): list(v or []) for k, v in hidden_subs.items()},
            "finance_categories": [
                {"id": str(row.get("id")), "label": str(row.get("label") or "").strip()}
                for row in (data.get("finance_categories") or [])
                if isinstance(row, dict) and row.get("id")
            ],
            "hidden_finance_categories": list(data.get("hidden_finance_categories") or []),
            "finance_types": _parse_finance_types(data.get("finance_types")),
            "hidden_finance_types": list(data.get("hidden_finance_types") or []),
        }
        if self._fs is not None:
            self._fs_set_meta("taxonomy", payload)
            return
        ensure_dirs()
        _TAXONOMY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def snapshot(self) -> dict[str, Any]:
        return {"folders": self.list_folders(), "subfolders": self.list_subfolders()}

    def list_folders(self) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        tax = self._load_taxonomy()
        hidden = {str(n) for n in (tax.get("hidden_folders") or [])}
        extra = [item.folder for item in self.list_items(limit=500)]
        custom = tax.get("folders") or []
        for name in [*FOLDERS, *custom, *extra]:
            if name and name not in seen and name not in hidden:
                seen.add(name)
                names.append(name)
        return names

    def list_subfolders(self) -> dict[str, list[str]]:
        tax = self._load_taxonomy()
        hidden_map = tax.get("hidden_subfolders") or {}
        merged: dict[str, list[str]] = {k: list(v) for k, v in SUBFOLDER_SEEDS.items()}
        for folder, names in (tax.get("subfolders") or {}).items():
            bucket = merged.setdefault(str(folder), [])
            for name in names or []:
                if name and name not in bucket:
                    bucket.append(name)
        for item in self.list_items(limit=500):
            if item.folder and item.subfolder:
                bucket = merged.setdefault(item.folder, [])
                if item.subfolder not in bucket:
                    bucket.append(item.subfolder)
        out: dict[str, list[str]] = {}
        for folder, names in merged.items():
            hidden = {str(n) for n in (hidden_map.get(folder) or [])}
            kept = [n for n in names if n and n not in hidden]
            if kept:
                out[folder] = kept
        return out

    def add_folder(self, name: str) -> str:
        clean = _clean_folder_name(name)
        if not clean:
            raise ValueError("Folder name is required")
        data = self._load_taxonomy()
        folders = list(data.get("folders") or [])
        if clean not in folders and clean not in FOLDERS:
            folders.append(clean)
        data["folders"] = folders
        data["hidden_folders"] = [n for n in (data.get("hidden_folders") or []) if n != clean]
        data.setdefault("subfolders", {}).setdefault(clean, [])
        self._save_taxonomy(data)
        return clean

    def add_subfolder(self, folder: str, name: str) -> str:
        parent = _clean_folder_name(folder)
        clean = _clean_folder_name(name)
        if not parent:
            raise ValueError("Parent folder is required")
        if not clean:
            raise ValueError("Subfolder name is required")
        if parent.lower() in _RESERVED_FOLDERS:
            raise ValueError("Pick a folder first")
        data = self._load_taxonomy()
        folders = list(data.get("folders") or [])
        if parent not in folders and parent not in FOLDERS:
            folders.append(parent)
        subs = dict(data.get("subfolders") or {})
        bucket = list(subs.get(parent) or [])
        if clean not in bucket:
            bucket.append(clean)
        subs[parent] = bucket
        data["folders"] = folders
        data["subfolders"] = subs
        hidden_subs = dict(data.get("hidden_subfolders") or {})
        hidden_subs[parent] = [n for n in (hidden_subs.get(parent) or []) if n != clean]
        data["hidden_subfolders"] = hidden_subs
        self._save_taxonomy(data)
        return clean

    def _rewrite_items(
        self,
        *,
        match_folder: str | None = None,
        match_subfolder: str | None = None,
        folder: str | None = None,
        subfolder: str | None = None,
    ) -> None:
        for item in self.list_items(limit=500):
            if match_folder is not None and item.folder != match_folder:
                continue
            if match_subfolder is not None and item.subfolder != match_subfolder:
                continue
            changed = False
            if folder is not None and item.folder != folder:
                item.folder = folder
                changed = True
            if subfolder is not None and item.subfolder != subfolder:
                item.subfolder = subfolder
                changed = True
            if changed:
                self.upsert(item)

    def rename_folder(self, folder: str, name: str) -> str:
        old = _clean_folder_name(folder)
        new = _clean_folder_name(name)
        if not old or not new:
            raise ValueError("Folder name is required")
        if old.lower() in _PROTECTED_FOLDERS:
            raise ValueError("Inbox cannot be renamed")
        if old == new:
            return new
        data = self._load_taxonomy()
        folders = [new if n == old else n for n in (data.get("folders") or [])]
        if new not in folders and new not in FOLDERS:
            folders.append(new)
        hidden = [n for n in (data.get("hidden_folders") or []) if n != new]
        if old in FOLDERS and old not in hidden:
            hidden.append(old)
        subs = dict(data.get("subfolders") or {})
        if old in subs:
            subs[new] = list(dict.fromkeys([*(subs.get(new) or []), *(subs.pop(old) or [])]))
        hidden_subs = dict(data.get("hidden_subfolders") or {})
        if old in hidden_subs:
            hidden_subs[new] = list(dict.fromkeys([*(hidden_subs.get(new) or []), *(hidden_subs.pop(old) or [])]))
        data["folders"] = folders
        data["hidden_folders"] = hidden
        data["subfolders"] = subs
        data["hidden_subfolders"] = hidden_subs
        self._save_taxonomy(data)
        self._rewrite_items(match_folder=old, folder=new)
        return new

    def delete_folder(self, folder: str) -> None:
        name = _clean_folder_name(folder)
        if not name:
            raise ValueError("Folder name is required")
        if name.lower() in _PROTECTED_FOLDERS:
            raise ValueError("Inbox cannot be deleted")
        data = self._load_taxonomy()
        data["folders"] = [n for n in (data.get("folders") or []) if n != name]
        hidden = list(data.get("hidden_folders") or [])
        if name not in hidden:
            hidden.append(name)
        data["hidden_folders"] = hidden
        subs = dict(data.get("subfolders") or {})
        subs.pop(name, None)
        data["subfolders"] = subs
        hidden_subs = dict(data.get("hidden_subfolders") or {})
        hidden_subs.pop(name, None)
        data["hidden_subfolders"] = hidden_subs
        self._save_taxonomy(data)
        self._rewrite_items(match_folder=name, folder="Inbox", subfolder="")

    def rename_subfolder(self, folder: str, subfolder: str, name: str) -> str:
        parent = _clean_folder_name(folder)
        old = _clean_folder_name(subfolder)
        new = _clean_folder_name(name)
        if not parent or not old or not new:
            raise ValueError("Subfolder name is required")
        if old == new:
            return new
        data = self._load_taxonomy()
        subs = dict(data.get("subfolders") or {})
        bucket = [new if n == old else n for n in (subs.get(parent) or [])]
        if new not in bucket:
            bucket.append(new)
        subs[parent] = bucket
        hidden_subs = dict(data.get("hidden_subfolders") or {})
        hidden = [n for n in (hidden_subs.get(parent) or []) if n != new]
        seeds = SUBFOLDER_SEEDS.get(parent) or []
        if old in seeds and old not in hidden:
            hidden.append(old)
        hidden_subs[parent] = hidden
        data["subfolders"] = subs
        data["hidden_subfolders"] = hidden_subs
        self._save_taxonomy(data)
        self._rewrite_items(match_folder=parent, match_subfolder=old, subfolder=new)
        return new

    def delete_subfolder(self, folder: str, subfolder: str) -> None:
        parent = _clean_folder_name(folder)
        name = _clean_folder_name(subfolder)
        if not parent or not name:
            raise ValueError("Subfolder name is required")
        data = self._load_taxonomy()
        subs = dict(data.get("subfolders") or {})
        subs[parent] = [n for n in (subs.get(parent) or []) if n != name]
        hidden_subs = dict(data.get("hidden_subfolders") or {})
        hidden = list(hidden_subs.get(parent) or [])
        if name not in hidden:
            hidden.append(name)
        hidden_subs[parent] = hidden
        data["subfolders"] = subs
        data["hidden_subfolders"] = hidden_subs
        self._save_taxonomy(data)
        self._rewrite_items(match_folder=parent, match_subfolder=name, subfolder="")

    def list_finance_categories(self) -> list[dict[str, str]]:
        tax = self._load_taxonomy()
        hidden = {str(n) for n in (tax.get("hidden_finance_categories") or [])}
        overrides = {
            str(row["id"]): str(row.get("label") or "").strip()
            for row in (tax.get("finance_categories") or [])
            if isinstance(row, dict) and row.get("id")
        }
        out: list[dict[str, str]] = []
        seen: set[str] = set()
        for cat_id in FINANCE_CATEGORIES:
            if cat_id in hidden:
                continue
            seen.add(cat_id)
            out.append({"id": cat_id, "label": overrides.get(cat_id, "")})
        for cat_id, label in overrides.items():
            if cat_id in seen or cat_id in hidden:
                continue
            seen.add(cat_id)
            out.append({"id": cat_id, "label": label})
        for item in self.list_items(limit=500):
            for fact in item.money():
                cat_id = str(fact.category or "").strip()
                if not cat_id or cat_id in seen or cat_id in hidden:
                    continue
                seen.add(cat_id)
                out.append({"id": cat_id, "label": overrides.get(cat_id, "")})
        return out

    def add_finance_category(self, name: str) -> dict[str, str]:
        label = _clean_category_label(name)
        slug = _slug_category(label)
        if not slug:
            raise ValueError("Category name is required")
        data = self._load_taxonomy()
        hidden = [n for n in (data.get("hidden_finance_categories") or []) if n != slug]
        rows = [
            row
            for row in (data.get("finance_categories") or [])
            if isinstance(row, dict) and row.get("id") and row["id"] != slug
        ]
        if slug not in FINANCE_CATEGORIES or label:
            rows.append({"id": slug, "label": label})
        data["finance_categories"] = rows
        data["hidden_finance_categories"] = hidden
        self._save_taxonomy(data)
        return {"id": slug, "label": label}

    def rename_finance_category(self, cat_id: str, name: str) -> dict[str, str]:
        old = _slug_category(cat_id) or str(cat_id or "").strip()
        label = _clean_category_label(name)
        if not old or not label:
            raise ValueError("Category name is required")
        data = self._load_taxonomy()
        hidden = list(data.get("hidden_finance_categories") or [])
        if old in hidden:
            hidden = [n for n in hidden if n != old]
        rows = [
            row
            for row in (data.get("finance_categories") or [])
            if isinstance(row, dict) and row.get("id") and row["id"] != old
        ]
        rows.append({"id": old, "label": label})
        data["finance_categories"] = rows
        data["hidden_finance_categories"] = hidden
        self._save_taxonomy(data)
        return {"id": old, "label": label}

    def delete_finance_category(self, cat_id: str) -> None:
        old = _slug_category(cat_id) or str(cat_id or "").strip()
        if not old:
            raise ValueError("Category name is required")
        if old == "outros":
            raise ValueError("Other cannot be deleted")
        data = self._load_taxonomy()
        data["finance_categories"] = [
            row
            for row in (data.get("finance_categories") or [])
            if not (isinstance(row, dict) and row.get("id") == old)
        ]
        hidden = list(data.get("hidden_finance_categories") or [])
        if old not in hidden:
            hidden.append(old)
        data["hidden_finance_categories"] = hidden
        self._save_taxonomy(data)
        self._rewrite_finance_category(old, "outros")

    def _rewrite_finance_category(self, old_id: str, new_id: str) -> None:
        if not old_id or old_id == new_id:
            return
        for item in self.list_items(limit=500):
            changed = False
            for fact in item.financials:
                if fact.category == old_id:
                    fact.category = new_id
                    changed = True
            if item.financial and item.financial.category == old_id:
                item.financial.category = new_id
                changed = True
            if changed:
                self.upsert(item)

    def list_finance_types(self) -> list[dict[str, str]]:
        tax = self._load_taxonomy()
        hidden = {str(n) for n in (tax.get("hidden_finance_types") or [])}
        overrides = {
            str(row["id"]): row
            for row in (tax.get("finance_types") or [])
            if isinstance(row, dict) and row.get("id")
        }
        out: list[dict[str, str]] = []
        seen: set[str] = set()
        for type_id, side in FINANCE_TYPES:
            if type_id in hidden:
                continue
            seen.add(type_id)
            extra = overrides.get(type_id) or {}
            out.append(
                {
                    "id": type_id,
                    "label": str(extra.get("label") or ""),
                    "side": extra.get("side") or side,
                }
            )
        for type_id, extra in overrides.items():
            if type_id in seen or type_id in hidden:
                continue
            seen.add(type_id)
            out.append(
                {
                    "id": type_id,
                    "label": str(extra.get("label") or ""),
                    "side": extra.get("side") or "saida",
                }
            )
        for item in self.list_items(limit=500):
            for fact in item.money():
                if (fact.bill_status or "").strip():
                    continue
                type_id = str(fact.kind or "").strip()
                if not type_id or type_id in {"desconhecido"} or type_id in seen or type_id in hidden:
                    continue
                seen.add(type_id)
                extra = overrides.get(type_id) or {}
                out.append(
                    {
                        "id": type_id,
                        "label": str(extra.get("label") or ""),
                        "side": extra.get("side") or ("entrada" if type_id == "receita" else "saida"),
                    }
                )
        return out

    def add_finance_type(self, name: str, side: str) -> dict[str, str]:
        label = _clean_category_label(name)
        slug = _slug_category(label)
        if not slug or slug == "desconhecido":
            raise ValueError("Type name is required")
        clean_side = _type_side(side)
        data = self._load_taxonomy()
        hidden = [n for n in (data.get("hidden_finance_types") or []) if n != slug]
        rows = [
            row
            for row in (data.get("finance_types") or [])
            if isinstance(row, dict) and row.get("id") and row["id"] != slug
        ]
        rows.append({"id": slug, "label": label, "side": clean_side})
        data["finance_types"] = rows
        data["hidden_finance_types"] = hidden
        self._save_taxonomy(data)
        return {"id": slug, "label": label, "side": clean_side}

    def rename_finance_type(self, type_id: str, name: str, side: str | None = None) -> dict[str, str]:
        old = _slug_category(type_id) or str(type_id or "").strip()
        label = _clean_category_label(name)
        if not old or not label:
            raise ValueError("Type name is required")
        data = self._load_taxonomy()
        current = next(
            (
                row
                for row in (data.get("finance_types") or [])
                if isinstance(row, dict) and row.get("id") == old
            ),
            None,
        )
        seed_side = next((side_ for type_id_, side_ in FINANCE_TYPES if type_id_ == old), "saida")
        clean_side = _type_side(side) if side else str((current or {}).get("side") or seed_side)
        hidden = [n for n in (data.get("hidden_finance_types") or []) if n != old]
        rows = [
            row
            for row in (data.get("finance_types") or [])
            if isinstance(row, dict) and row.get("id") and row["id"] != old
        ]
        rows.append({"id": old, "label": label, "side": clean_side})
        data["finance_types"] = rows
        data["hidden_finance_types"] = hidden
        self._save_taxonomy(data)
        return {"id": old, "label": label, "side": clean_side}

    def delete_finance_type(self, type_id: str) -> None:
        old = _slug_category(type_id) or str(type_id or "").strip()
        if not old:
            raise ValueError("Type name is required")
        if old in {"receita", "gasto"}:
            raise ValueError("Income and expense cannot be deleted")
        data = self._load_taxonomy()
        current = next(
            (
                row
                for row in self.list_finance_types()
                if row["id"] == old
            ),
            None,
        )
        fallback = "receita" if current and current.get("side") == "entrada" else "gasto"
        data["finance_types"] = [
            row
            for row in (data.get("finance_types") or [])
            if not (isinstance(row, dict) and row.get("id") == old)
        ]
        hidden = list(data.get("hidden_finance_types") or [])
        if old not in hidden:
            hidden.append(old)
        data["hidden_finance_types"] = hidden
        self._save_taxonomy(data)
        self._rewrite_finance_type(old, fallback)

    def _rewrite_finance_type(self, old_id: str, new_id: str) -> None:
        if not old_id or old_id == new_id:
            return
        for item in self.list_items(limit=500):
            changed = False
            for fact in item.financials:
                if fact.kind == old_id and not (fact.bill_status or "").strip():
                    fact.kind = new_id
                    changed = True
            if item.financial and item.financial.kind == old_id and not (item.financial.bill_status or "").strip():
                item.financial.kind = new_id
                changed = True
            if changed:
                self.upsert(item)

    def _load_accounting(self) -> dict[str, Any]:
        raw: dict[str, Any] = {}
        if self._fs is not None:
            raw = self._fs_meta("accounting")
        else:
            ensure_dirs()
            if _ACCOUNTING.exists():
                try:
                    raw = json.loads(_ACCOUNTING.read_text(encoding="utf-8") or "{}")
                except json.JSONDecodeError:
                    raw = {}
        months: dict[str, dict[str, Any]] = {}
        for key, row in (raw.get("months") or {}).items():
            if not isinstance(row, dict):
                continue
            month = normalize_month(str(key))
            if str(key)[:7] != month:
                continue
            expenses = []
            for exp in row.get("expenses") or []:
                if not isinstance(exp, dict) or not exp.get("id"):
                    continue
                try:
                    amount = parse_money(exp.get("amount") or 0, allow_blank=True)
                except ValueError:
                    amount = 0.0
                expenses.append(
                    {
                        "id": str(exp["id"]),
                        "description": str(exp.get("description") or "").strip()[:80],
                        "amount": amount,
                    }
                )
            try:
                revenue = parse_money(row.get("revenue") or 0, allow_blank=True)
            except ValueError:
                revenue = 0.0
            try:
                distribution = parse_money(row.get("distribution") or 0, allow_blank=True)
            except ValueError:
                distribution = 0.0
            months[month] = {"revenue": revenue, "distribution": distribution, "expenses": expenses}
        return {"months": months}

    def _save_accounting(self, data: dict[str, Any]) -> None:
        payload = {"months": data.get("months") or {}}
        if self._fs is not None:
            self._fs_set_meta("accounting", payload)
            return
        ensure_dirs()
        _ACCOUNTING.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _blank_accounting_month(self) -> dict[str, Any]:
        return {"revenue": 0.0, "distribution": 0.0, "expenses": []}

    def accounting_view(self, month: str | None = None) -> dict[str, Any]:
        data = self._load_accounting()
        key = normalize_month(month)
        record = data["months"].get(key) or self._blank_accounting_month()
        keys = set(data["months"].keys())
        keys.add(key)
        rows = []
        for mk in order_months(list(keys)):
            summary = compute(data["months"].get(mk) or self._blank_accounting_month())
            rows.append(
                {
                    "month": mk,
                    "revenue": summary["revenue"],
                    "payments": summary["payments"],
                    "profit": summary["profit"],
                    "distribution": summary["distribution"],
                    "movement": summary["movement"],
                    "expenses_total": summary["expenses_total"],
                }
            )
        return {
            "month": key,
            "input": {
                "revenue": record.get("revenue") or 0,
                "distribution": record.get("distribution") or 0,
                "expenses": list(record.get("expenses") or []),
            },
            "sheet": compute(record),
            "months": rows,
        }

    def save_accounting_month(self, month: str | None, revenue, distribution) -> dict[str, Any]:
        with _lock:
            data = self._load_accounting()
            key = normalize_month(month)
            row = data["months"].get(key) or self._blank_accounting_month()
            row["revenue"] = parse_money(revenue, allow_blank=True)
            row["distribution"] = parse_money(distribution, allow_blank=True)
            data["months"][key] = row
            self._save_accounting(data)
        return self.accounting_view(key)

    def add_accounting_expense(self, month: str | None, description: str, amount) -> dict[str, Any]:
        parsed = parse_money(amount)
        if parsed <= 0:
            raise ValueError("invalid amount")
        label = clean_description(description)
        with _lock:
            data = self._load_accounting()
            key = normalize_month(month)
            row = data["months"].get(key) or self._blank_accounting_month()
            row["expenses"] = list(row.get("expenses") or [])
            row["expenses"].append({"id": new_id("acx"), "description": label, "amount": parsed})
            data["months"][key] = row
            self._save_accounting(data)
        return self.accounting_view(key)

    def update_accounting_expense(self, month: str | None, expense_id: str, description: str, amount) -> dict[str, Any]:
        parsed = parse_money(amount)
        if parsed <= 0:
            raise ValueError("invalid amount")
        label = clean_description(description)
        with _lock:
            data = self._load_accounting()
            key = normalize_month(month)
            row = data["months"].get(key) or self._blank_accounting_month()
            found = False
            expenses = []
            for exp in row.get("expenses") or []:
                if str(exp.get("id")) == expense_id:
                    expenses.append({"id": expense_id, "description": label, "amount": parsed})
                    found = True
                else:
                    expenses.append(exp)
            if not found:
                raise ValueError("expense not found")
            row["expenses"] = expenses
            data["months"][key] = row
            self._save_accounting(data)
        return self.accounting_view(key)

    def delete_accounting_expense(self, month: str | None, expense_id: str) -> dict[str, Any]:
        with _lock:
            data = self._load_accounting()
            key = normalize_month(month)
            row = data["months"].get(key) or self._blank_accounting_month()
            before = list(row.get("expenses") or [])
            row["expenses"] = [exp for exp in before if str(exp.get("id")) != expense_id]
            if len(row["expenses"]) == len(before):
                raise ValueError("expense not found")
            data["months"][key] = row
            self._save_accounting(data)
        return self.accounting_view(key)


def _clean_folder_name(name: str) -> str:
    cleaned = " ".join((name or "").replace("/", "-").replace("\\", "-").split())
    cleaned = cleaned.strip()[:60]
    if cleaned.lower() in _RESERVED_FOLDERS:
        return ""
    return cleaned


def _clean_category_label(name: str) -> str:
    cleaned = " ".join((name or "").split()).strip()[:40]
    return cleaned


def _parse_finance_types(rows) -> list[dict[str, str]]:
    out = []
    for row in rows or []:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        side = "entrada" if str(row.get("side") or "") == "entrada" else "saida"
        out.append({"id": str(row["id"]), "label": str(row.get("label") or "").strip(), "side": side})
    return out


def _type_side(value: str) -> str:
    text = (value or "").strip().lower()
    if text in {"entrada", "credito", "crédito", "receita", "income", "credit"}:
        return "entrada"
    return "saida"


def _slug_category(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:40]


store = Store()
