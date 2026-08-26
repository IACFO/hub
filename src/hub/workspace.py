from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from hub.config import CLIENT_SECRET_PATH, TOKEN_PATH, ensure_dirs

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def load_user_credentials() -> Credentials | None:
    ensure_dirs()
    creds: Credentials | None = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    if creds and creds.valid:
        return creds
    return None


def interactive_login() -> Credentials:
    if not CLIENT_SECRET_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CLIENT_SECRET_PATH}. Download the Desktop OAuth client JSON "
            "from Google Cloud Console and save it there."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
    creds = flow.run_local_server(port=8085, prompt="consent")
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def create_calendar_event(
    title: str,
    start: str,
    end: str | None = None,
    description: str = "",
) -> dict:
    creds = load_user_credentials()
    if creds is None:
        return {
            "status": "pending_local",
            "message": "OAuth ainda nao configurado. Evento ficou proposto no Hub.",
            "title": title,
            "start": start,
        }
    from googleapiclient.discovery import build

    end_iso = end or _plus_one_hour(start)
    body = {
        "summary": title,
        "description": description or "Criado pelo Hub agent",
        "start": {"dateTime": _as_rfc3339(start), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": _as_rfc3339(end_iso), "timeZone": "America/Sao_Paulo"},
    }
    service = build("calendar", "v3", credentials=creds)
    created = service.events().insert(calendarId="primary", body=body).execute()
    return {
        "status": "created",
        "event_id": created.get("id"),
        "html_link": created.get("htmlLink"),
        "title": title,
        "start": start,
    }


def upload_drive_file(path: str, folder_name: str = "Hub") -> dict:
    creds = load_user_credentials()
    if creds is None:
        return {"status": "skipped", "message": "OAuth nao configurado para Drive."}
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    service = build("drive", "v3", credentials=creds)
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    found = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    files = found.get("files", [])
    if files:
        folder_id = files[0]["id"]
    else:
        folder = (
            service.files()
            .create(
                body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
                fields="id",
            )
            .execute()
        )
        folder_id = folder["id"]
    media = MediaFileUpload(path, resumable=True)
    created = (
        service.files()
        .create(
            body={"name": Path(path).name, "parents": [folder_id]},
            media_body=media,
            fields="id, webViewLink",
        )
        .execute()
    )
    return {
        "status": "uploaded",
        "file_id": created.get("id"),
        "link": created.get("webViewLink"),
    }


def _plus_one_hour(start: str) -> str:
    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    return (dt + timedelta(hours=1)).isoformat()


def _as_rfc3339(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
