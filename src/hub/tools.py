from __future__ import annotations

import re

from hub.schema import (
    AgentTraceStep,
    CalendarProposal,
    Category,
    CheckItem,
    EmailProposal,
    FinancialFact,
    InboxItem,
    Priority,
    TaskItem,
    now_iso,
)

_CATEGORIES = {
    "tarefas",
    "lembretes",
    "financas",
    "conhecimento",
    "saude",
    "ideias",
    "documentos",
    "compras",
    "treino",
    "prompts",
    "links",
    "outros",
}
_CATEGORY_ALIASES = {
    "finanças": "financas",
    "financeiro": "financas",
    "finance": "financas",
    "task": "tarefas",
    "tasks": "tarefas",
    "reminder": "lembretes",
    "knowledge": "conhecimento",
    "health": "saude",
    "saúde": "saude",
    "idea": "ideias",
    "docs": "documentos",
    "documento": "documentos",
    "shop": "compras",
    "compras": "compras",
    "gym": "treino",
    "academia": "treino",
    "suno": "prompts",
    "instagram": "links",
}
_KINDS = {
    "note",
    "task",
    "link",
    "document",
    "shopping",
    "workout",
    "prompt",
    "finance",
    "media",
}
_STATUSES = {"inbox", "active", "done", "discarded"}


def _category(value: str) -> Category:
    raw = (value or "outros").strip().lower()
    raw = _CATEGORY_ALIASES.get(raw, raw)
    return raw if raw in _CATEGORIES else "outros"  # type: ignore[return-value]

def _normalize_folder(value: str | None) -> str | None:
    if not value:
        return None
    name = re.sub(r"\s+", " ", value.strip())[:32]
    if not re.fullmatch(r"[\wÀ-ÿ][\wÀ-ÿ \-]*", name, flags=re.I):
        return None
    return name


from pathlib import Path

from hub.store import store
from hub.workspace import (
    create_calendar_event,
    has_gmail_send,
    load_user_credentials,
    send_gmail,
    upload_drive_file,
)


def save_inbox_item(
    user_id: str,
    summary: str,
    category: Category,
    raw_text: str = "",
    tags: list[str] | None = None,
    key_insights: list[str] | None = None,
    item_id: str | None = None,
    folder: str | None = None,
    kind: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    url: str | None = None,
    body: str | None = None,
    subfolder: str | None = None,
) -> dict:
    """Persist a structured inbox item. Call this once per capture after extracting meaning."""
    item = store.get(item_id) if item_id else None
    if item is None:
        item = InboxItem(user_id=user_id)
        if item_id:
            item.id = item_id
    item.summary = summary
    item.category = _category(category)
    mapped = {
        "compras": ("Compras", "shopping"),
        "treino": ("Treino", "workout"),
        "prompts": ("Prompts", "prompt"),
        "links": ("Links", "link"),
        "documentos": ("Documentos", "document"),
        "financas": ("Financas", "finance"),
        "tarefas": ("Agenda", "task"),
        "lembretes": ("Agenda", "task"),
        "saude": ("Saude", "note"),
        "ideias": ("Ideias", "note"),
    }.get(item.category)
    if mapped and not folder:
        item.folder = mapped[0]
        if not kind:
            item.kind = mapped[1]  # type: ignore[assignment]
    item.raw_text = raw_text or item.raw_text
    item.tags = tags or item.tags
    item.key_insights = key_insights or item.key_insights
    named = _normalize_folder(folder)
    if named:
        item.folder = named
    sub = _normalize_folder(subfolder)
    if sub:
        item.subfolder = sub
    if kind and kind in _KINDS:
        item.kind = kind  # type: ignore[assignment]
    if title:
        item.title = title
    if subtitle:
        item.subtitle = subtitle
    if url:
        item.url = url
    if body:
        item.body = body
    item.trace.append(AgentTraceStep(kind="save_inbox_item", detail=summary))
    store.upsert(item)
    return {"status": "saved", "item_id": item.id, "category": item.category, "folder": item.folder}


def add_shopping_items(item_id: str, items: list[str], list_name: str = "Compras") -> dict:
    """Turn extracted grocery/shopping lines into a checklist. Use for 'comprar leite, pão...'."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    for line in items:
        text = (line or "").strip(" -•*")
        if text:
            item.checklist.append(CheckItem(text=text))
    item.kind = "shopping"
    item.folder = "Compras"
    item.category = "compras"
    if list_name and not item.title:
        item.title = list_name
    item.trace.append(AgentTraceStep(kind="shopping", detail=", ".join(items)[:200]))
    store.upsert(item)
    return {"status": "saved", "count": len(item.checklist), "item_id": item_id}


def organize_item(
    item_id: str,
    folder: str,
    kind: str = "note",
    title: str | None = None,
    subtitle: str | None = None,
    url: str | None = None,
    subfolder: str | None = None,
) -> dict:
    """Put the capture in a theme folder. Use a known folder or create a short new one (Fotos, Musica)."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    named = _normalize_folder(folder)
    if named:
        item.folder = named
    if kind in _KINDS:
        item.kind = kind  # type: ignore[assignment]
    if title:
        item.title = title
    if subtitle:
        item.subtitle = subtitle
    if url:
        item.url = url
    sub = _normalize_folder(subfolder)
    if sub:
        item.subfolder = sub
    item.status = "active"
    item.trace.append(AgentTraceStep(kind="organize", detail=f"{item.folder}/{item.kind}"))
    store.upsert(item)
    return {"status": "saved", "folder": item.folder, "kind": item.kind}


def set_item_status(item_id: str, status: str) -> dict:
    """Mark an item inbox | active | done | discarded."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    if status not in _STATUSES:
        return {"status": "error", "message": "invalid status"}
    item.status = status  # type: ignore[assignment]
    item.trace.append(AgentTraceStep(kind="status", detail=status))
    store.upsert(item)
    return {"status": "saved", "item_status": item.status}


def add_task(
    item_id: str,
    description: str,
    due_at: str | None = None,
    priority: Priority = "media",
) -> dict:
    """Attach an actionable task extracted from the capture."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    task = TaskItem(description=description, due_at=due_at, priority=priority)
    item.tasks.append(task)
    item.trace.append(AgentTraceStep(kind="add_task", detail=description))
    store.upsert(item)
    return {"status": "proposed", "task_id": task.id, "item_id": item_id}


def propose_calendar_event(
    item_id: str,
    title: str,
    start: str,
    end: str | None = None,
    description: str = "",
) -> dict:
    """Propose a calendar event. It is NOT written to Google Calendar until confirm_calendar_event."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    event = CalendarProposal(title=title, start=start, end=end, description=description)
    item.calendar.append(event)
    item.trace.append(AgentTraceStep(kind="propose_calendar", detail=f"{title} @ {start}"))
    store.upsert(item)
    oauth = load_user_credentials() is not None
    return {
        "status": "proposed",
        "event_id": event.id,
        "item_id": item_id,
        "needs_confirmation": True,
        "google_calendar_ready": oauth,
    }


def confirm_calendar_event(item_id: str, event_id: str) -> dict:
    """Write a proposed event to Google Calendar. Call only after the user confirms."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    for event in item.calendar:
        if event.id == event_id:
            result = create_calendar_event(
                title=event.title,
                start=event.start,
                end=event.end,
                description=event.description,
            )
            event.status = "confirmed" if result.get("status") == "created" else "proposed"
            event.calendar_event_id = result.get("event_id")
            item.trace.append(
                AgentTraceStep(kind="confirm_calendar", detail=str(result.get("status")))
            )
            store.upsert(item)
            return {"event_id": event.id, **result}
    return {"status": "error", "message": "calendar proposal not found"}


def save_financial_fact(
    item_id: str,
    amount: float | None = None,
    merchant: str | None = None,
    due_at: str | None = None,
    kind: str = "desconhecido",
    barcode: str | None = None,
    category: str = "outros",
    occurred_at: str | None = None,
) -> dict:
    """Append a money line (gasto, boleto or receita). Call once per amount in the capture."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    kind_norm = (kind or "desconhecido").lower()
    if kind_norm not in {"gasto", "boleto", "receita", "desconhecido"}:
        kind_norm = "desconhecido"
    cat = (category or "outros").lower()
    from hub.schema import FINANCE_CATEGORIES

    if cat not in FINANCE_CATEGORIES:
        cat = "renda" if kind_norm == "receita" else "outros"
    fact = FinancialFact(
        amount=amount,
        merchant=merchant,
        due_at=due_at,
        occurred_at=occurred_at or due_at,
        category=cat,
        kind=kind_norm,  # type: ignore[assignment]
        barcode=barcode,
    )
    item.financials.append(fact)
    item.financial = fact
    item.folder = "Financas"
    item.kind = "finance"
    if kind_norm == "receita":
        item.subfolder = item.subfolder or "Receitas"
    elif kind_norm == "boleto":
        item.subfolder = item.subfolder or "Boletos"
    else:
        item.subfolder = item.subfolder or "Gastos"
    item.trace.append(
        AgentTraceStep(kind="financial", detail=f"{kind} {merchant} {amount} due {due_at}")
    )
    store.upsert(item)
    return {"status": "saved", "item_id": item_id, "count": len(item.financials), "financial": fact.model_dump()}


def search_inbox(query: str, user_id: str) -> dict:
    """Search previously captured items by text, tags, or task description."""
    hits = store.search(query, user_id=user_id)
    return {
        "count": len(hits),
        "items": [
            {
                "id": h.id,
                "summary": h.summary,
                "category": h.category,
                "tags": h.tags,
                "created_at": h.created_at,
            }
            for h in hits
        ],
    }


def list_pending_actions(user_id: str) -> dict:
    """List proposed tasks and calendar events waiting for confirmation."""
    pending: list[dict] = []
    for item in store.list_items(user_id=user_id, limit=100):
        for task in item.tasks:
            if task.status == "proposed":
                pending.append(
                    {
                        "kind": "task",
                        "item_id": item.id,
                        "id": task.id,
                        "description": task.description,
                        "due_at": task.due_at,
                    }
                )
        for event in item.calendar:
            if event.status == "proposed":
                pending.append(
                    {
                        "kind": "calendar",
                        "item_id": item.id,
                        "id": event.id,
                        "title": event.title,
                        "start": event.start,
                    }
                )
    return {"count": len(pending), "pending": pending}


def attach_media_to_drive(item_id: str, path: str) -> dict:
    """Upload original media to the user's Google Drive Hub folder."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    result = upload_drive_file(path, folder_name="Hub")
    item.trace.append(AgentTraceStep(kind="drive_upload", detail=str(result.get("status"))))
    store.upsert(item)
    return result


def today_iso() -> dict:
    """Return the current UTC timestamp so relative dates (tomorrow 14:00) can be resolved."""
    return {"now": now_iso(), "timezone": "America/Sao_Paulo"}


def list_user_documents(user_id: str) -> dict:
    """List documents already in Hub (CV, CNH, PDFs) so you can attach the right file."""
    docs = []
    for item in store.list_items(user_id=user_id, limit=200):
        if item.kind == "document" or item.folder == "Documentos":
            docs.append(
                {
                    "id": item.id,
                    "title": item.title or item.summary,
                    "has_file": bool(item.media_paths),
                }
            )
    return {"documents": docs}


def _find_cv(user_id: str) -> tuple[str | None, str]:
    scored: list[tuple[int, str]] = []
    for item in store.list_items(user_id=user_id, limit=200):
        blob = f"{item.title} {item.summary} {' '.join(item.tags)}".lower()
        if not item.media_paths:
            continue
        score = 0
        if any(w in blob for w in ("curriculo", "currículo", "resume")) or re.search(
            r"\bcv\b", blob
        ):
            score += 5
        if item.folder == "Documentos":
            score += 1
        if score >= 5:
            scored.append((score, item.media_paths[0]))
    scored.sort(reverse=True)
    if not scored:
        return None, ""
    path = scored[0][1]
    return path, Path(path).name


def _find_cv_path(user_id: str) -> str | None:
    path, _ = _find_cv(user_id)
    return path


def propose_email(
    item_id: str,
    to: str,
    subject: str,
    body: str,
    attach_cv: bool = True,
) -> dict:
    """Draft a CV email. Telegram asks twice before sending. Never send from this tool."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    proposal = EmailProposal(to=to.strip(), subject=subject, body=body, attach_cv=attach_cv)
    item.emails.append(proposal)
    cv_path, cv_name = _find_cv(item.user_id)
    item.trace.append(AgentTraceStep(kind="propose_email", detail=f"{to} cv={bool(cv_path)}"))
    store.upsert(item)
    return {
        "status": "proposed",
        "email_id": proposal.id,
        "to": proposal.to,
        "cv_found": cv_path is not None,
        "cv_name": cv_name,
        "gmail_ready": has_gmail_send(load_user_credentials()),
        "needs_two_step_confirmation": True,
    }


def mark_email_preview(item_id: str, email_id: str) -> dict:
    """First Telegram yes: freeze the draft so the user can read it before send."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    for proposal in item.emails:
        if proposal.id != email_id:
            continue
        if proposal.status not in {"proposed", "preview"}:
            return {"status": "error", "message": f"email already {proposal.status}"}
        proposal.status = "preview"
        cv_path, cv_name = _find_cv(item.user_id)
        item.trace.append(AgentTraceStep(kind="email_preview", detail=proposal.to))
        store.upsert(item)
        return {
            "status": "preview",
            "email_id": proposal.id,
            "to": proposal.to,
            "subject": proposal.subject,
            "body": proposal.body,
            "attach_cv": proposal.attach_cv,
            "cv_found": cv_path is not None,
            "cv_name": cv_name or "(nenhum arquivo de CV encontrado)",
        }
    return {"status": "error", "message": "email proposal not found"}


def confirm_email(item_id: str, email_id: str) -> dict:
    """Send only after the user approved the preview."""
    item = store.get(item_id)
    if item is None:
        return {"status": "error", "message": f"item {item_id} not found"}
    for proposal in item.emails:
        if proposal.id != email_id:
            continue
        if proposal.status != "preview":
            return {
                "status": "error",
                "message": "aprove o preview do email antes de enviar",
            }
        attachment = _find_cv_path(item.user_id) if proposal.attach_cv else None
        result = send_gmail(proposal.to, proposal.subject, proposal.body, attachment)
        if result.get("status") == "sent":
            proposal.status = "confirmed"
            proposal.gmail_id = result.get("gmail_id")
        item.trace.append(AgentTraceStep(kind="confirm_email", detail=str(result.get("status"))))
        store.upsert(item)
        return {"email_id": proposal.id, **result}
    return {"status": "error", "message": "email proposal not found"}


HUB_TOOLS = [
    save_inbox_item,
    add_task,
    add_shopping_items,
    organize_item,
    set_item_status,
    propose_calendar_event,
    confirm_calendar_event,
    propose_email,
    list_user_documents,
    save_financial_fact,
    search_inbox,
    list_pending_actions,
    attach_media_to_drive,
    today_iso,
]
