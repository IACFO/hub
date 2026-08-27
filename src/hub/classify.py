from __future__ import annotations

import re

from hub.schema import FOLDER_FROM_CATEGORY, CheckItem, InboxItem

_URL = re.compile(r"https?://[^\s<>\)]+", re.I)
_DOC_WORDS = re.compile(
    r"\b(cnh|habilita[cç][aã]o|passaporte|curr[ií]culo|curriculo|comprovante|contrato)\b",
    re.I,
)
_SHOP_HINTS = ("comprar", "compras", "lista de compra", "feira")
_MONEY_HINTS = ("gastei", "recebi", "salario", "salário", "boleto", "pix", "r$")
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
        [text, item.raw_text, item.summary, item.body, item.subtitle, " ".join(item.tags), item.title]
    ).lower()
    tags = {t.lower() for t in item.tags}
    locked = bool(item.folder and item.folder not in {"Inbox", ""})

    if not item.url:
        item.url = extract_url(text) or extract_url(item.raw_text)

    if item.money():
        item.kind = "finance"
        item.folder = "Financas"
        item.category = "financas"
    elif (item.checklist or tags & _SHOP_TAGS or any(h in blob for h in _SHOP_HINTS)) and not any(
        h in blob for h in _MONEY_HINTS
    ):
        item.kind = "shopping"
        if not locked:
            item.folder = "Compras"
        item.category = "compras"
    elif (
        item.kind == "workout"
        or tags & _WORK_TAGS
        or any(h in blob for h in _WORK_HINTS)
    ):
        item.kind = "workout"
        if not locked:
            item.folder = "Treino"
        item.category = "treino"
    elif item.kind == "prompt" or tags & _PROMPT_TAGS or any(h in blob for h in _PROMPT_HINTS):
        item.kind = "prompt"
        if not locked:
            item.folder = "Prompts"
        item.category = "prompts"
    elif item.url or item.media_type == "link" or item.kind == "link":
        item.kind = "link"
        if not locked:
            item.folder = "Links"
        item.category = "links"
        if item.url and "instagram.com" in item.url:
            item.tags = _uniq(item.tags + ["instagram"])
    elif item.media_type == "document" or item.kind == "document" or _DOC_WORDS.search(blob):
        item.kind = "document"
        if not locked:
            item.folder = "Documentos"
        item.category = "documentos"
    elif item.calendar or item.tasks:
        item.kind = "task"
        if not locked:
            item.folder = "Agenda"
        item.category = "tarefas"
    elif item.media_type == "photo":
        if _DOC_WORDS.search(blob) or item.folder == "Documentos":
            item.kind = "document"
            item.folder = "Documentos"
            item.category = "documentos"
        else:
            item.kind = "media"
            item.folder = "Fotos"
            if not item.title:
                item.title = (item.raw_text or item.summary or "Foto")[:80]
    elif item.media_type == "audio":
        item.kind = "media"
        if not locked or item.folder == "Inbox":
            item.folder = "Musica"
        if not item.title:
            item.title = (item.raw_text or "Audio")[:80]
    elif item.media_type == "voice":
        if item.kind == "note":
            item.kind = "media"
        if not locked:
            item.folder = FOLDER_FROM_CATEGORY.get(item.category, "Inbox")
    elif not locked:
        item.folder = FOLDER_FROM_CATEGORY.get(item.category, "Inbox")

    if not item.title:
        item.title = item.display_title()
    if item.raw_text and not item.body and item.kind in {"workout", "prompt", "note"}:
        item.body = item.raw_text
    if item.status == "inbox" and (item.calendar or item.checklist or item.money()):
        item.status = "active"
    if not item.subfolder:
        item.subfolder = _guess_subfolder(item, blob)
    return item


def _guess_subfolder(item: InboxItem, blob: str) -> str:
    rules = {
        "Fotos": [
            (("print", "screenshot", "captura", "tela"), "Prints"),
            (("selfie", "eu na", "foto minha"), "Selfies"),
            (("capa", "cover", "set "), "Capas"),
        ],
        "Links": [
            (("vaga", "job", "hiring", "curriculo", "cv"), "Vagas"),
            (("noticia", "news", "jornal"), "Noticias"),
            (("filme", "serie", "show", "youtube", "entreten"), "Entretenimento"),
        ],
        "Ideias": [
            (("trabalho", "carreira", "projeto", "hub"), "Profissional"),
            (("andamento", "wip", "fazendo"), "Andamento"),
            (("insight", "notei", "percebi"), "Insights"),
        ],
        "Financas": [
            (("boleto",), "Boletos"),
            (("recebi", "pix", "salario", "receita"), "Receitas"),
            (("gastei", "paguei", "compra"), "Gastos"),
        ],
    }
    for hints, name in rules.get(item.folder, []):
        if any(h in blob for h in hints):
            return name
    if item.folder == "Fotos":
        return "Pessoal"
    if item.folder == "Ideias":
        return "Pessoal"
    return ""


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
