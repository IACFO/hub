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
    "https://www.googleapis.com/auth/gmail.send",
]
GMAIL_SEND = "https://www.googleapis.com/auth/gmail.send"


def load_user_credentials() -> Credentials | None:
    ensure_dirs()
    creds: Credentials | None = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), scopes=SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        try:
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        except OSError:
            pass
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


def has_gmail_send(creds: Credentials | None) -> bool:
    if creds is None:
        return False
    granted = set(creds.scopes or [])
    return GMAIL_SEND in granted


def send_gmail(
    to: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> dict:
    creds = load_user_credentials()
    if creds is None:
        return {"status": "pending_local", "message": "OAuth nao configurado."}
    if not has_gmail_send(creds):
        return {
            "status": "needs_gmail_oauth",
            "message": "Falta permissao gmail.send. Rode python scripts/auth_workspace.py de novo.",
            "to": to,
        }
    import base64
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    from googleapiclient.discovery import build

    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))
    attached = False
    if attachment_path:
        from hub.media import read_bytes

        try:
            payload = read_bytes(attachment_path)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "message": f"nao consegui ler o CV: {exc}",
                "to": to,
            }
        if not payload:
            return {"status": "error", "message": "arquivo do CV esta vazio", "to": to}
        name = attachment_path.rstrip("/").rsplit("/", 1)[-1] or "cv.pdf"
        main, sub = ("application", "pdf") if name.lower().endswith(".pdf") else ("application", "octet-stream")
        part = MIMEBase(main, sub)
        part.set_payload(payload)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=name)
        message.attach(part)
        attached = True
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service = build("gmail", "v1", credentials=creds)
    try:
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    except Exception as exc:
        detail = str(exc)
        if "accessNotConfigured" in detail or "Gmail API has not been used" in detail:
            return {
                "status": "gmail_api_disabled",
                "message": "Gmail API desligada no projeto GCP. Ligue gmail.googleapis.com e tente de novo.",
                "to": to,
            }
        return {"status": "error", "message": detail[:400], "to": to}
    return {
        "status": "sent",
        "gmail_id": sent.get("id"),
        "to": to,
        "subject": subject,
        "attached": attached,
    }


def _plus_one_hour(start: str) -> str:
    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    return (dt + timedelta(hours=1)).isoformat()


def _as_rfc3339(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
