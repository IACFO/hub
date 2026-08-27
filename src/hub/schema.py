from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

Category = Literal[
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
]
Priority = Literal["alta", "media", "baixa"]
ActionStatus = Literal["proposed", "preview", "confirmed", "done", "cancelled", "failed"]
MediaType = Literal["text", "voice", "audio", "photo", "document", "link", "mixed"]
ItemKind = Literal[
    "note",
    "task",
    "link",
    "document",
    "shopping",
    "workout",
    "prompt",
    "finance",
    "media",
]
ItemStatus = Literal["inbox", "active", "done", "discarded"]

FOLDERS = [
    "Inbox",
    "Agenda",
    "Financas",
    "Compras",
    "Documentos",
    "Links",
    "Treino",
    "Prompts",
    "Ideias",
    "Saude",
    "Fotos",
    "Musica",
]

SUBFOLDER_SEEDS = {
    "Fotos": ["Selfies", "Prints", "Capas", "Pessoal"],
    "Ideias": ["Pessoal", "Profissional", "Andamento", "Insights", "Curiosidades"],
    "Links": ["Vagas", "Entretenimento", "Curiosidades", "Noticias"],
    "Financas": ["Gastos", "Receitas", "Boletos"],
}

FINANCE_CATEGORIES = (
    "alimentacao",
    "transporte",
    "casa",
    "saude",
    "renda",
    "lazer",
    "outros",
)

FOLDER_FROM_CATEGORY = {
    "tarefas": "Agenda",
    "lembretes": "Agenda",
    "financas": "Financas",
    "conhecimento": "Ideias",
    "saude": "Saude",
    "ideias": "Ideias",
    "documentos": "Documentos",
    "compras": "Compras",
    "treino": "Treino",
    "prompts": "Prompts",
    "links": "Links",
    "outros": "Inbox",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str = "itm") -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class TaskItem(BaseModel):
    id: str = Field(default_factory=lambda: new_id("tsk"))
    description: str
    due_at: str | None = None
    priority: Priority = "media"
    status: ActionStatus = "proposed"


class CalendarProposal(BaseModel):
    id: str = Field(default_factory=lambda: new_id("cal"))
    title: str
    start: str
    end: str | None = None
    description: str = ""
    status: ActionStatus = "proposed"
    calendar_event_id: str | None = None


class FinancialFact(BaseModel):
    id: str = Field(default_factory=lambda: new_id("fin"))
    amount: float | None = None
    currency: str = "BRL"
    merchant: str | None = None
    due_at: str | None = None
    occurred_at: str | None = None
    category: str = "outros"
    kind: Literal["gasto", "boleto", "receita", "desconhecido"] = "desconhecido"
    barcode: str | None = None


class CheckItem(BaseModel):
    id: str = Field(default_factory=lambda: new_id("chk"))
    text: str
    checked: bool = False


class AgentTraceStep(BaseModel):
    at: str = Field(default_factory=now_iso)
    kind: str
    detail: str


class EmailProposal(BaseModel):
    id: str = Field(default_factory=lambda: new_id("eml"))
    to: str
    subject: str
    body: str = ""
    attach_cv: bool = True
    status: ActionStatus = "proposed"
    gmail_id: str | None = None


class InboxItem(BaseModel):
    id: str = Field(default_factory=lambda: new_id("itm"))
    user_id: str
    source: str = "telegram"
    media_type: MediaType = "text"
    kind: ItemKind = "note"
    status: ItemStatus = "inbox"
    folder: str = "Inbox"
    subfolder: str = ""
    title: str = ""
    subtitle: str = ""
    url: str | None = None
    body: str = ""
    raw_text: str = ""
    summary: str = ""
    category: Category = "outros"
    tags: list[str] = Field(default_factory=list)
    tasks: list[TaskItem] = Field(default_factory=list)
    calendar: list[CalendarProposal] = Field(default_factory=list)
    checklist: list[CheckItem] = Field(default_factory=list)
    emails: list[EmailProposal] = Field(default_factory=list)
    financial: FinancialFact | None = None
    financials: list[FinancialFact] = Field(default_factory=list)
    key_insights: list[str] = Field(default_factory=list)
    media_paths: list[str] = Field(default_factory=list)
    telegram_chat_id: int | None = None
    telegram_message_id: int | None = None
    agent_reply: str = ""
    trace: list[AgentTraceStep] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def _sync_financials(self):
        if self.financial and not self.financials:
            self.financials = [self.financial]
        elif self.financials and not self.financial:
            self.financial = self.financials[0]
        return self

    def display_title(self) -> str:
        return self.title or self.summary or (self.raw_text[:80] if self.raw_text else self.id)

    def money(self) -> list[FinancialFact]:
        if self.financials:
            return self.financials
        return [self.financial] if self.financial else []
