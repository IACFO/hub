"""Monthly PJ sheet: pró-labore, INSS, IR 2026, DAS and available profit."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Anexo III with Fator R: pró-labore at 28% of revenue keeps DAS at 6%.
PROLABORE_RATE = 0.28
INSS_RATE = 0.11
# Teto do salário de contribuição a partir de 1/1/2026 (Portaria MPS/MF nº 13/2026).
INSS_CEILING = 8475.55
DAS_RATE = 0.06

# Tabela mensal do IRRF a partir de janeiro/2026. Limite da base, alíquota, parcela a deduzir.
IR_BRACKETS = (
    (2428.80, 0.0, 0.0),
    (2826.65, 0.075, 182.16),
    (3751.05, 0.15, 394.16),
    (4664.68, 0.225, 675.49),
    (10**12, 0.275, 908.73),
)


def current_month() -> str:
    now = datetime.now(timezone(timedelta(hours=-3)))
    return now.strftime("%Y-%m")


def normalize_month(month: str | None) -> str:
    raw = (month or "").strip()[:7]
    if len(raw) == 7 and raw[4] == "-" and raw[:4].isdigit() and raw[5:7].isdigit():
        if 1 <= int(raw[5:7]) <= 12:
            return raw
    return current_month()


def order_months(keys: list[str], today: str | None = None) -> list[str]:
    anchor = today or current_month()
    ordered = sorted({key for key in keys if key})
    upcoming = [key for key in ordered if key >= anchor]
    past = [key for key in reversed(ordered) if key < anchor]
    return [*upcoming, *past]


def money(value: float) -> float:
    return round(float(value) + 1e-9, 2)


def parse_money(value, *, allow_blank: bool = False) -> float:
    if value is None or value == "":
        if allow_blank:
            return 0.0
        raise ValueError("invalid amount")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid amount") from exc
    if number < 0 or number != number or number == float("inf"):
        raise ValueError("invalid amount")
    return money(number)


def clean_description(text: str) -> str:
    cleaned = " ".join((text or "").split()).strip()[:80]
    if not cleaned:
        raise ValueError("description required")
    return cleaned


def irrf(base: float, taxable_income: float) -> float:
    """Monthly withholding. Taxable income up to R$ 5,000 is exempt in 2026."""
    tax = 0.0
    for limit, rate, deduction in IR_BRACKETS:
        if base <= limit + 1e-9:
            tax = max(0.0, base * rate - deduction)
            break
    if taxable_income <= 5000 + 1e-9:
        return 0.0
    if taxable_income <= 7350 + 1e-9:
        reduction = 978.62 - (0.133145 * taxable_income)
        tax = max(0.0, tax - max(0.0, reduction))
    return money(tax)


def compute(record: dict | None) -> dict:
    record = record or {}
    revenue = money(max(0.0, float(record.get("revenue") or 0)))
    prolabore = money(revenue * PROLABORE_RATE)
    inss_base = money(min(prolabore, INSS_CEILING))
    inss = money(inss_base * INSS_RATE)
    ir = irrf(money(prolabore - inss), prolabore)
    net = money(prolabore - inss - ir)
    das = money(revenue * DAS_RATE)
    expenses = []
    for row in record.get("expenses") or []:
        if not isinstance(row, dict):
            continue
        expenses.append(
            {
                "id": str(row.get("id") or ""),
                "description": str(row.get("description") or "").strip(),
                "amount": money(max(0.0, float(row.get("amount") or 0))),
            }
        )
    expenses_total = money(sum(row["amount"] for row in expenses))
    profit = money(revenue - prolabore - das - expenses_total)
    distribution = money(max(0.0, float(record.get("distribution") or 0)))
    payments = money(prolabore + das + expenses_total + distribution)
    return {
        "revenue": revenue,
        "prolabore_gross": prolabore,
        "inss_base": inss_base,
        "inss": inss,
        "ir": ir,
        "prolabore_net": net,
        "das": das,
        "expenses": expenses,
        "expenses_total": expenses_total,
        "profit": profit,
        "distribution": distribution,
        "after_distribution": money(profit - distribution),
        "receipts": revenue,
        "payments": payments,
        "movement": money(revenue - payments),
    }
