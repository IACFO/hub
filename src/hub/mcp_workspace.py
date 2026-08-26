from __future__ import annotations

import os
from datetime import datetime, timedelta

import google.auth
from google.auth.transport.requests import Request
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from hub.workspace import load_user_credentials

os.environ.setdefault("ADK_ENABLE_MCP_GRACEFUL_ERROR_HANDLING", "1")


class _TokenRelay:
    def __init__(self, credentials):
        self._creds = credentials
        self._cached: str | None = None
        self._expiry: datetime | None = None

    def get_token(self) -> str:
        now = datetime.now()
        if (
            self._cached is None
            or self._expiry is None
            or now >= self._expiry - timedelta(minutes=5)
        ):
            self._creds.refresh(Request())
            self._cached = self._creds.token
            self._expiry = now + timedelta(minutes=50)
        return self._cached or ""


def workspace_toolsets() -> list:
    creds = load_user_credentials()
    if creds is None:
        creds, _ = google.auth.default()
    relay = _TokenRelay(creds)
    relay.get_token()

    def headers(_tool_context=None) -> dict[str, str]:
        return {"Authorization": f"Bearer {relay.get_token()}"}

    endpoints = {
        "calendar": "https://calendarmcp.googleapis.com/mcp/v1",
        "drive": "https://drivemcp.googleapis.com/mcp/v1",
        "gmail": "https://gmailmcp.googleapis.com/mcp/v1",
    }
    return [
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=url),
            header_provider=headers,
        )
        for url in endpoints.values()
    ]
