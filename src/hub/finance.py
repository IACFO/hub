from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from hub.schema import FinancialFact, InboxItem

_TZ = timezone(timedelta(hours=-3))


def _month_key(value: str | None, fallback: str) -> str:
    raw = (value or fallback or "")[:10]
    if len(raw) >= 7 and raw[4] == "-":
        return raw[:7]
    return fallback[:7]


def _fact_month(item: InboxItem, fact) -> str:
    stamp = fact.occurred_at or fact.due_at or item.created_at
    return _month_key(stamp, item.created_at)


def month_summary(items: list[InboxItem], month: str | None = None) -> dict:
    now = datetime.now(_TZ).strftime("%Y-%m")
    target = (month or now)[:7]
    income = 0.0
    expense = 0.0
    by_cat: dict[str, float] = defaultdict(float)
    rows = []
    for item in items:
        for fact in item.money():
            if _fact_month(item, fact) != target:
                continue
            amount = float(fact.amount or 0)
            kind = fact.kind
            if kind == "receita":
                income += amount
                by_cat[fact.category or "renda"] += amount
            else:
                expense += amount
                by_cat[fact.category or "outros"] += amount
            rows.append(
                {
                    "item_id": item.id,
                    "title": item.display_title(),
                    "kind": kind,
                    "category": fact.category,
                    "merchant": fact.merchant,
                    "amount": amount,
                    "occurred_at": fact.occurred_at or fact.due_at or item.created_at[:10],
                    "folder": item.folder,
                    "subfolder": item.subfolder,
                }
            )
    rows.sort(key=lambda r: r["occurred_at"], reverse=True)
    return {
        "month": target,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
        "by_category": {k: round(v, 2) for k, v in sorted(by_cat.items())},
        "entries": rows,
        "count": len(rows),
    }


def week_agenda(items: list[InboxItem]) -> dict:
    now = datetime.now(_TZ)
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=7)
    tasks = []
    events = []
    for item in items:
        for task in item.tasks:
            due = (task.due_at or "")[:10]
            if due and start.strftime("%Y-%m-%d") <= due < end.strftime("%Y-%m-%d"):
                tasks.append(task.description)
        for event in item.calendar:
            when = (event.start or "")[:10]
            if when and start.strftime("%Y-%m-%d") <= when < end.strftime("%Y-%m-%d"):
                events.append(event.title)
    return {
        "week_start": start.strftime("%Y-%m-%d"),
        "tasks": tasks[:20],
        "events": events[:20],
        "folders": _folder_counts(items),
    }


def reports_snapshot(items: list[InboxItem]) -> dict:
    now = datetime.now(_TZ)
    week_ago = now - timedelta(days=7)
    recent = 0
    pending_cal = 0
    pending_mail = 0
    folders: dict[str, int] = defaultdict(int)
    tags: dict[str, int] = defaultdict(int)
    for item in items:
        created = item.created_at or ""
        if created >= week_ago.isoformat():
            recent += 1
        folders[item.folder] += 1
        for tag in item.tags:
            tags[tag.lower()] += 1
        pending_cal += sum(1 for e in item.calendar if e.status == "proposed")
        pending_mail += sum(1 for e in item.emails if e.status in {"proposed", "preview"})
    top_tags = sorted(tags.items(), key=lambda kv: kv[1], reverse=True)[:8]
    return {
        "captures_7d": recent,
        "pending_calendar": pending_cal,
        "pending_email": pending_mail,
        "folders": dict(sorted(folders.items(), key=lambda kv: kv[1], reverse=True)),
        "top_tags": [{"tag": k, "n": v} for k, v in top_tags],
        "agenda": week_agenda(items),
    }


def _folder_counts(items: list[InboxItem]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        if item.status in {"inbox", "active"}:
            counts[item.folder] += 1
    return dict(counts)


_FOOD = {"restaurante", "almoco", "almoço", "mercado", "feira", "ifood", "lanche", "padaria"}
_RECEIVE = re.compile(
    r"recebi(?:\s+\w+){0,4}\s+(\d+(?:[.,]\d+)?)\s*(mil)?",
    re.I,
)
_SPEND_AT = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:reais|r\$)?\s*(?:no|na|em)\s+([a-záàâãéêíóôõúç]+)",
    re.I,
)


def parse_money_text(text: str, occurred_at: str | None = None) -> list[FinancialFact]:
    """Best-effort parse when the LLM is down. Does not invent extra amounts."""
    if not text:
        return []
    today = occurred_at or datetime.now(_TZ).strftime("%Y-%m-%d")
    facts: list[FinancialFact] = []
    lowered = text.lower()
    for match in _RECEIVE.finditer(text):
        amount = float(match.group(1).replace(",", "."))
        if match.group(2):
            amount *= 1000
        merchant = "salario" if "salar" in lowered else "recebimento"
        facts.append(
            FinancialFact(
                amount=amount,
                kind="receita",
                category="renda",
                merchant=merchant,
                occurred_at=today,
            )
        )
    if "gastei" in lowered or "paguei" in lowered:
        for match in _SPEND_AT.finditer(text):
            amount = float(match.group(1).replace(",", "."))
            merchant = match.group(2).lower()
            if merchant in {"hoje", "ontem", "salario", "salário"}:
                continue
            cat = "alimentacao" if merchant in _FOOD else "outros"
            facts.append(
                FinancialFact(
                    amount=amount,
                    kind="gasto",
                    category=cat,
                    merchant=merchant,
                    occurred_at=today,
                )
            )
    return facts


def apply_money_fallback(item: InboxItem, text: str = "") -> InboxItem:
    if item.money():
        return item
    facts = parse_money_text(text or item.raw_text, occurred_at=(item.created_at or "")[:10])
    if not facts:
        return item
    item.financials.extend(facts)
    item.financial = facts[0]
    item.kind = "finance"
    item.folder = "Financas"
    item.category = "financas"
    item.status = "active"
    if not item.title:
        item.title = "Movimentação financeira"
    return item
