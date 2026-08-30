# Hub — Inbox-to-Life

Personal multimodal organizer for the [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/) (**Taskmaster** track).

Dump voice, photos, invoices, PDFs, links, or text into Telegram. An agent (Google ADK + Gemini 3.6 Flash on Vertex) classifies, files into themed folders, and proposes Calendar / Gmail actions you confirm in the chat. A Cloud Run dashboard lets you browse the archive (EN/PT toggle).

**Live demo:** https://hub-451649651313.us-central1.run.app

Architecture diagram: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Stack

- Gemini 3.6 Flash via **Vertex AI** (`GOOGLE_CLOUD_LOCATION=global`)
- Google ADK agent + tools
- Telegram capture (webhook on Cloud Run)
- Google Calendar + Gmail + Drive (OAuth, confirm-before-send)
- Firestore + Cloud Storage
- Gemma (filing hints), Veo (week recap), Lyria (week theme)
- Local JSON fallback when Firestore/GCS are off

## Local spin-up

Prerequisites: Python 3.11+, a Telegram bot token, and either Vertex ADC or an AI Studio key. Detailed connector checklist (OAuth, APIs): [docs/SETUP.md](docs/SETUP.md).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# fill TELEGRAM_BOT_TOKEN and GCP / Gemini settings in .env
$env:PYTHONPATH = "src"
python scripts/check_setup.py
```

Run the dashboard:

```powershell
$env:PYTHONPATH = "src"
python -m hub.server
# open http://localhost:8080
```

Run Telegram **locally with polling** (do not do this while the Cloud Run webhook is active — polling calls `deleteWebhook`):

```powershell
$env:PYTHONPATH = "src"
python -m hub.telegram_bot
```

Optional OAuth for Calendar / Gmail / Drive:

```powershell
# place credentials/client_secret.json (Desktop OAuth client)
python scripts/auth_workspace.py
# writes credentials/token.json
```

ADK web (agent debug): from `agents/`, run `adk web --port 8000`.

### Useful `.env` flags

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | BotFather token |
| `GOOGLE_CLOUD_PROJECT` | GCP project id |
| `GOOGLE_CLOUD_LOCATION` | Use `global` for Gemini on Vertex |
| `GOOGLE_GENAI_USE_VERTEXAI` | `true` for Vertex credits |
| `HUB_USE_FIRESTORE` | `true` in cloud, `false` for local JSON |
| `GCS_BUCKET` | Media bucket name |
| `GEMINI_MODEL` | Default `gemini-3.6-flash` |

## Cloud Run spin-up

Script: [`scripts/deploy_cloud_run.ps1`](scripts/deploy_cloud_run.ps1).

What it does:

1. Enables Run, Vertex, Firestore, Storage, Secret Manager, Gmail APIs
2. Syncs `credentials/token.json` into Secret Manager (`hub-oauth-token`)
3. Deploys from source with env vars + secrets (`TELEGRAM_BOT_TOKEN`, mounted OAuth token)
4. Prints the service URL

```powershell
# requires gcloud + credentials/token.json + telegram-bot-token secret
.\scripts\deploy_cloud_run.ps1
```

After deploy, point the Telegram webhook at:

`https://<your-service>.run.app/telegram/webhook`

The service binds `0.0.0.0:$PORT` (FastAPI / uvicorn). Filesystem is ephemeral — use Firestore + GCS in production (`HUB_USE_FIRESTORE=true`).

## How to demo

1. Open the live dashboard (EN by default; switch to PT with the rail toggle).
2. Send the bot a voice note, a LinkedIn job link, a photo, or “gastei 40 no almoço”.
3. Confirm Calendar / CV email buttons in Telegram when offered.
4. Watch the card land under Archive / Finance / Reports.

## Reproducible testing

### Hosted (fastest for judges)

1. Open **https://hub-451649651313.us-central1.run.app**
2. Confirm the UI loads in **English** (toggle **EN/PT** in the top-right on mobile, or in the left rail on desktop).
3. Browse **Archive / Finance / Reports** — cards come from live Firestore captures.
4. Watch the demo video (YouTube, English captions via CC) for Telegram → agent → Calendar confirm end-to-end.

Telegram write-actions (send new captures / Confirm buttons) require the project bot token and the submitter’s Google OAuth token; judges can validate the hosted dashboard + video without those secrets.

### Local

1. Follow **Local spin-up** above (`pip install`, `.env`, `PYTHONPATH=src`).
2. `python scripts/check_setup.py`
3. `python -m hub.server` → http://localhost:8080
4. Optional: `python -m hub.telegram_bot` **only if** the Cloud Run webhook is disabled (`deleteWebhook` otherwise).
5. Optional Calendar/Gmail: `python scripts/auth_workspace.py` after placing `credentials/client_secret.json`.

Cloud Run redeploy: `.\scripts\deploy_cloud_run.ps1` (see **Cloud Run spin-up**).

## License

Hackathon submission — see Devpost entry for details.
