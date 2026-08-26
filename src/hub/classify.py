from __future__ import annotations

import re

from hub.schema import FOLDER_FROM_CATEGORY, CheckItem, InboxItem

_URL = re.compile(r"https?://[^\s<>\)]+", re.I)
_DOC_WORDS = re.compile(
    r"\b(cnh|habilita[cç][aã]o|passaporte|curr[ií]culo|curriculo|comprovante|contrato)\b",
    re.I,
)
_SHOP_HINTS = ("comprar", "compras", "lista de compra", "mercado", "feira")
_WORK_HINTS = (
    "treino",
    "academia",
    "supino",
    "hipertrofia",
    "ficha de treino",
    "abcde",
    "leg press",
)
_PROMPT_HINTS = ("suno", "midjourney", "stable diffusion", "gera uma musica", "gerar música")
_WORK_TAGS = {"treino", "academia", "fitness", "hipertrofia", "workout"}
_SHOP_TAGS = {"compras", "mercado", "feira"}
_PROMPT_TAGS = {"suno", "prompt", "midjourney"}


def extract_url(text: str) -> str | None:
    if not text:
        return None
    match = _URL.search(text)
    return match.group(0).rstrip(".,);") if match else None


def enrich(item: InboxItem, text: str = "") -> InboxItem:
    blob = " ".join(
        [text, item.raw_text, item.summary, item.body, " ".join(item.tags), item.title]
    ).lower()
    tags = {t.lower() for t in item.tags}

    if not item.url:
        item.url = extract_url(text) or extract_url(item.raw_text)

    if item.financial:
        item.kind = "finance"
        item.folder = "Financas"
        item.category = "financas"
    elif item.checklist or tags & _SHOP_TAGS or any(h in blob for h in _SHOP_HINTS):
        item.kind = "shopping"
        item.folder = "Compras"
        item.category = "compras"
    elif (
        item.kind == "workout"
        or tags & _WORK_TAGS
        or any(h in blob for h in _WORK_HINTS)
    ):
        item.kind = "workout"
        item.folder = "Treino"
        item.category = "treino"
    elif item.kind == "prompt" or tags & _PROMPT_TAGS or any(h in blob for h in _PROMPT_HINTS):
        item.kind = "prompt"
        item.folder = "Prompts"
        item.category = "prompts"
    elif item.url or item.media_type == "link" or item.kind == "link":
        item.kind = "link"
        item.folder = "Links"
        item.category = "links"
        if item.url and "instagram.com" in item.url:
            item.tags = _uniq(item.tags + ["instagram"])
    elif item.media_type == "document" or item.kind == "document" or _DOC_WORDS.search(blob):
        item.kind = "document"
        item.folder = "Documentos"
        item.category = "documentos"
    elif item.calendar or item.tasks:
        item.kind = "task"
        item.folder = "Agenda"
        item.category = "tarefas"
    elif item.media_type in {"photo", "voice", "audio"}:
        if item.kind == "note":
            item.kind = "media"
        if item.folder == "Inbox":
            item.folder = FOLDER_FROM_CATEGORY.get(item.category, "Inbox")
    elif item.folder == "Inbox":
        item.folder = FOLDER_FROM_CATEGORY.get(item.category, "Inbox")

    if not item.title:
        item.title = item.display_title()
    if item.raw_text and not item.body and item.kind in {"workout", "prompt", "note"}:
        item.body = item.raw_text
    if item.status == "inbox" and (item.calendar or item.checklist or item.financial):
        item.status = "active"
    return item


def lines_to_checklist(lines: list[str]) -> list[CheckItem]:
    items = []
    for line in lines:
        text = line.strip(" -•*\t")
        if text:
            items.append(CheckItem(text=text))
    return items


def _uniq(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out
