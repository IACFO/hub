from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx

_EMAIL = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_OG = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_OG2 = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
    re.I,
)
_DESC = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = " ".join(data.split())
            if text:
                self._chunks.append(text)

    def text(self) -> str:
        return " ".join(self._chunks)


def fetch_url_context(url: str) -> dict:
    """Best-effort page read. LinkedIn often returns a login wall."""
    result = {
        "url": url,
        "ok": False,
        "title": "",
        "description": "",
        "emails": [],
        "snippet": "",
        "login_walled": False,
    }
    try:
        with httpx.Client(follow_redirects=True, timeout=10.0) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                },
            )
        html = response.text or ""
        lowered = html.lower()
        result["ok"] = response.status_code < 400
        title = _first(_OG.search(html), _OG2.search(html), _TITLE.search(html))
        result["title"] = _clean(title)
        desc = _DESC.search(html)
        result["description"] = _clean(desc.group(1) if desc else "")
        result["emails"] = sorted(
            {
                m.group(0).lower()
                for m in _EMAIL.finditer(html)
                if not m.group(0).lower().endswith(("@linkedin.com", "@lnkd.in"))
            }
        )[:8]
        extractor = _TextExtractor()
        try:
            extractor.feed(html)
            result["snippet"] = extractor.text()[:2500]
        except Exception:
            result["snippet"] = re.sub(r"<[^>]+>", " ", html)[:1500]
        result["login_walled"] = any(
            token in lowered
            for token in ("sign in", "entrar", "login", "authwall", "join now")
        ) and "linkedin" in lowered
        if result["login_walled"] and "linkedin" in (result["title"] or "").lower():
            result["title"] = ""
    except Exception as exc:  # noqa: BLE001
        result["snippet"] = f"(falha ao abrir URL: {exc})"
    return result


def _first(*matches) -> str:
    for match in matches:
        if match:
            return match.group(1)
    return ""


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()
