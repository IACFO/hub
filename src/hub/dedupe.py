"""Collapse duplicate link/job captures (same URL, LinkedIn post, or same vaga)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

from hub.classify import extract_url
from hub.schema import AgentTraceStep, InboxItem
from hub.store import store

_TRACKING = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "originalsubdomain",
    "si",
    "trackingid",
    "trk",
    "utm_campaign",
    "utm_content",
    "utm_id",
    "utm_medium",
    "utm_source",
    "utm_term",
}

_EMAIL = re.compile(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", re.I)
_LI_ACTIVITY = re.compile(
    r"(?:activity-|urn:li:(?:activity|ugcpost|share):)(\d{10,})",
    re.I,
)
_LI_JOB = re.compile(r"linkedin\.com/jobs/view/(\d+)", re.I)
_GENERIC_TITLE = re.compile(
    r"^(publica[cç][aã]o no linkedin|link do linkedin|linkedin|link salvo|p[aá]gina requer login)",
    re.I,
)
_WALL = re.compile(
    r"requer login|login wall|p[aá]gina requer login|join now|sign in to|authwall",
    re.I,
)
_PERSON = re.compile(
    r"(?:por|by)\s+([A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+){1,2})"
)
_DASH_NAME = re.compile(
    r"[—–]\s*([A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+)"
)
_ROLES = (
    "ai engineer",
    "engenheiro de ia",
    "ml engineer",
    "machine learning",
    "data scientist",
    "cientista de dados",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
)

_STOP = {
    "vaga",
    "vagas",
    "de",
    "da",
    "do",
    "para",
    "no",
    "na",
    "em",
    "com",
    "por",
    "o",
    "a",
    "e",
    "remoto",
    "clt",
    "pj",
    "linkedin",
    "publicacao",
    "publicação",
    "link",
    "pasta",
    "links",
    "post",
    "the",
    "and",
}
_NOT_NAMES = _STOP | {
    "pagina",
    "página",
    "login",
    "requer",
}


def canonical_url(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if "safelinks.protection.outlook.com" in host:
        inner = dict(parse_qsl(parsed.query, keep_blank_values=True)).get("url")
        if inner:
            return canonical_url(unquote(inner))
    if not host:
        return raw.rstrip("/").lower()
    path = parsed.path.rstrip("/") or "/"
    pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in _TRACKING and not k.lower().startswith("utm_")
    ]
    return urlunparse(("https", host, path, "", urlencode(pairs), ""))


def linkedin_key(url: str | None) -> str | None:
    blob = url or ""
    activity = _LI_ACTIVITY.search(blob)
    if activity:
        return f"li:{activity.group(1)}"
    job = _LI_JOB.search(blob)
    if job:
        return f"job:{job.group(1)}"
    return None


def looks_like_link_capture(url: str | None, text: str, media_type: str = "text") -> bool:
    if url or media_type == "link":
        return True
    blob = (text or "").lower()
    if "linkedin.com" in blob or "lnkd.in" in blob:
        return True
    return "vaga" in blob and any(
        token in blob for token in ("linkedin", "curriculo", "currículo", "envie", "cv ")
    )


def capture_is_richer(existing: InboxItem, incoming: InboxItem) -> bool:
    return _text_weight(incoming) > _text_weight(existing) + 40


def find_link_duplicate(
    user_id: str,
    *,
    url: str | None,
    text: str,
    exclude_id: str | None = None,
) -> InboxItem | None:
    keys = _capture_keys(url, text)
    candidates: list[InboxItem] = []
    for item in _link_items(user_id):
        if exclude_id and item.id == exclude_id:
            continue
        item_ks = _item_keys(item)
        if keys and keys & item_ks:
            candidates.append(item)
            continue
        if _same_job(text, item):
            candidates.append(item)
    if not candidates:
        return None
    return max(candidates, key=_richness)


def merge_capture(keeper: InboxItem, incoming: InboxItem) -> InboxItem:
    if incoming.url and (not keeper.url or _is_thin(keeper)):
        keeper.url = incoming.url
    if _text_weight(incoming) > _text_weight(keeper):
        keeper.raw_text = incoming.raw_text or keeper.raw_text
    if incoming.body and len(incoming.body) > len(keeper.body or "") and not _is_thin_text(incoming.body):
        keeper.body = incoming.body
    if incoming.summary and len(incoming.summary) > len(keeper.summary or "") and not _is_thin_text(
        incoming.summary
    ):
        keeper.summary = incoming.summary
    if incoming.title and (
        not keeper.title or _GENERIC_TITLE.match(keeper.title or "") or _is_thin(keeper)
    ):
        keeper.title = incoming.title
        if incoming.subtitle:
            keeper.subtitle = incoming.subtitle
    if incoming.subtitle and (not keeper.subtitle or _GENERIC_TITLE.match(keeper.subtitle or "")):
        keeper.subtitle = incoming.subtitle
    keeper.tags = list(dict.fromkeys([*keeper.tags, *incoming.tags]))[:8]
    if incoming.emails and not keeper.emails:
        keeper.emails = incoming.emails
    if incoming.media_paths:
        keeper.media_paths = list(dict.fromkeys([*keeper.media_paths, *incoming.media_paths]))
    keeper.trace.append(
        AgentTraceStep(kind="dedupe", detail=f"merged from {incoming.id or 'new-capture'}")
    )
    return keeper


def collapse_user_links(user_id: str) -> int:
    items = _link_items(user_id)
    if len(items) < 2:
        return 0
    parent = {item.id: item.id for item in items}

    def find(xid: str) -> str:
        while parent[xid] != xid:
            parent[xid] = parent[parent[xid]]
            xid = parent[xid]
        return xid

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    buckets: dict[str, list[str]] = {}
    for item in items:
        for key in _item_keys(item):
            buckets.setdefault(key, []).append(item.id)
    for ids in buckets.values():
        first = ids[0]
        for other in ids[1:]:
            union(first, other)

    remaining = list(items)
    for i, left in enumerate(remaining):
        for right in remaining[i + 1 :]:
            if find(left.id) == find(right.id):
                continue
            if _item_keys(left) & _item_keys(right) or _same_job(_item_blob(left), right):
                union(left.id, right.id)

    groups: dict[str, list[InboxItem]] = {}
    for item in items:
        groups.setdefault(find(item.id), []).append(item)

    discarded = 0
    for group in groups.values():
        if len(group) < 2:
            continue
        keeper = max(group, key=_richness)
        for other in group:
            if other.id == keeper.id:
                continue
            keeper = merge_capture(keeper, other)
            other.status = "discarded"
            if "duplicado" not in other.tags:
                other.tags = [*(other.tags or []), "duplicado"]
            other.trace.append(AgentTraceStep(kind="dedupe", detail=f"duplicate of {keeper.id}"))
            store.upsert(other)
            discarded += 1
        store.upsert(keeper)
    return discarded


def collapse_all_links() -> int:
    items = store.list_items(limit=400)
    users = {item.user_id for item in items if item.user_id}
    return sum(collapse_user_links(user_id) for user_id in users)


def _link_items(user_id: str) -> list[InboxItem]:
    out: list[InboxItem] = []
    for item in store.list_items(user_id=user_id, limit=200):
        if item.status == "discarded":
            continue
        if _is_linkish(item):
            out.append(item)
    return out


def _is_linkish(item: InboxItem) -> bool:
    if item.kind == "link" or item.media_type == "link" or item.folder == "Links":
        return True
    url = item.url or extract_url(item.raw_text or "")
    if not url:
        return False
    return item.kind not in {"document", "finance", "media"}


def _item_blob(item: InboxItem) -> str:
    return " ".join(
        part
        for part in (
            item.title,
            item.subtitle,
            item.summary,
            item.body,
            item.raw_text,
            item.url or "",
            " ".join(item.tags),
        )
        if part
    )


def _capture_keys(url: str | None, text: str) -> set[str]:
    keys: set[str] = set()
    canon = canonical_url(url or extract_url(text))
    if canon:
        keys.add(f"url:{canon}")
        li = linkedin_key(canon) or linkedin_key(url) or linkedin_key(text)
        if li:
            keys.add(li)
    sig = _job_sig(text)
    if sig:
        keys.add(f"sig:{sig}")
    return keys


def _item_keys(item: InboxItem) -> set[str]:
    return _capture_keys(item.url, _item_blob(item))


def _same_job(text: str, item: InboxItem) -> bool:
    incoming_sig = _job_sig(text)
    item_blob = _item_blob(item)
    item_sig = _job_sig(item_blob)
    if _sigs_match(incoming_sig, item_sig):
        return True
    incoming_norm = _norm(text)
    item_norm = _norm(item_blob)
    role = _role_slug(incoming_norm)
    band = _salary_band(incoming_norm)
    if role and band and role == _role_slug(item_norm) and band == _salary_band(item_norm):
        person_in = _person_slug(text)
        person_item = _person_slug(item_blob)
        compact_in = incoming_norm.replace(" ", "")
        compact_item = item_norm.replace(" ", "")
        if person_in and person_in in compact_item:
            return True
        if person_item and person_item in compact_in:
            return True
        mails_in = {mail.lower() for mail in _EMAIL.findall(text or "")}
        mails_item = {mail.lower() for mail in _EMAIL.findall(item_blob)}
        if mails_in & mails_item:
            return True
    if _is_thin_text(text) or _GENERIC_TITLE.match((item.title or "").strip()):
        return False
    left = _norm_title(text[:240])
    right = _norm_title(f"{item.title} {item.subtitle}")
    if len(left) < 18 or len(right) < 12:
        return False
    title_ratio = SequenceMatcher(None, left, right).ratio()
    summary_ratio = SequenceMatcher(
        None, _norm_title(text[:400]), _norm_title(item.summary or item.body or "")
    ).ratio()
    return max(title_ratio, summary_ratio) >= 0.72


def _sigs_match(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    shared = set(left.split("|")) & set(right.split("|"))
    return len(shared) >= 2


def _job_sig(text: str) -> str:
    blob = _norm(text)
    if not blob:
        return ""
    emails = [
        mail.lower()
        for mail in _EMAIL.findall(text or "")
        if not mail.lower().endswith(("@linkedin.com", "@lnkd.in"))
    ]
    bits: list[str] = []
    if emails:
        bits.append("m:" + emails[0])
    person = _person_slug(text)
    if person:
        bits.append("p:" + person)
    role = _role_slug(blob)
    band = _salary_band(blob)
    if role and band:
        bits.append(f"r:{role}:{band}")
    elif role:
        bits.append("r:" + role)
    if len(bits) < 2:
        return ""
    return "|".join(sorted(bits))


def _person_slug(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        match = _PERSON.search(line) or _DASH_NAME.search(line)
        if not match:
            continue
        parts = [part for part in _norm(match.group(1)).split() if part not in _NOT_NAMES]
        if len(parts) >= 2:
            return "".join(parts[:3])
    return ""


def _role_slug(blob: str) -> str:
    for role in _ROLES:
        if role in blob:
            return role.replace(" ", "")
    return ""


def _salary_band(blob: str) -> str:
    compact = blob.replace(".", "").replace(" ", "")
    match = re.search(r"(\d{1,3})k[-–aà]+(\d{1,3})k", compact)
    if match:
        return f"{int(match.group(1))}-{int(match.group(2))}"
    match = re.search(r"r\$(\d{4,6})(?:a|ate|até|–|-)(?:r\$)?(\d{4,6})", compact)
    if match:
        return f"{int(match.group(1)) // 1000}-{int(match.group(2)) // 1000}"
    return ""


def _norm(text: str) -> str:
    lowered = (text or "").lower()
    return re.sub(r"[^a-z0-9@$.\-]+", " ", lowered).strip()


def _norm_title(text: str) -> str:
    words = [word for word in _norm(text).split() if word not in _STOP and len(word) > 2]
    return " ".join(words)


def _is_thin_text(text: str) -> bool:
    blob = text or ""
    if _WALL.search(blob):
        return True
    stripped = re.sub(r"https?://\S+", "", blob)
    stripped = _norm(stripped)
    return len(stripped) < 40


def _is_thin(item: InboxItem) -> bool:
    return _is_thin_text(" ".join(part for part in (item.body, item.summary, item.raw_text, item.title) if part))


def _text_weight(item: InboxItem) -> int:
    blob = " ".join(part for part in (item.body, item.summary, item.raw_text) if part)
    stripped = re.sub(r"https?://\S+", "", blob)
    if _is_thin_text(blob):
        return min(len(stripped), 30)
    return len(stripped.strip())


def _richness(item: InboxItem) -> tuple:
    return (
        0 if _is_thin(item) else 1,
        _text_weight(item),
        len(item.title or ""),
        1 if item.url else 0,
        item.created_at or "",
    )
