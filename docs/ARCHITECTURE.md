# Hub architecture

Personal multimodal organizer for the [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/) (Taskmaster track).

Capture chaos on Telegram → an ADK agent on Vertex Gemini classifies and files it → confirm Calendar / Gmail actions → review on a Cloud Run dashboard.

```mermaid
flowchart LR
  subgraph Capture
    U[User]
    TG[Telegram Bot]
  end

  subgraph CloudRun["Cloud Run · hub"]
    API[FastAPI · webhook + dashboard]
    ADK[Google ADK agent]
    Tools[Hub tools]
  end

  subgraph Vertex["Vertex AI · global"]
    Gemini[Gemini 3.6 Flash]
    Gemma[Gemma filing hints]
    Veo[Veo week recap]
    Lyria[Lyria week theme]
  end

  subgraph Store
    FS[(Firestore inbox)]
    GCS[(Cloud Storage media)]
  end

  subgraph Workspace["Google Workspace · user OAuth"]
    Cal[Calendar]
    Gmail[Gmail]
    Drive[Drive]
  end

  U -->|voice photo PDF link text| TG
  TG -->|HTTPS webhook| API
  API --> ADK
  ADK --> Gemini
  ADK --> Tools
  Tools --> Gemma
  Tools --> FS
  Tools --> GCS
  Tools -->|propose then confirm| Cal
  Tools -->|propose then confirm| Gmail
  Tools --> Drive
  API -->|Veo / Lyria buttons| Veo
  API --> Lyria
  U -->|dashboard EN/PT| API
```

## Request path

1. Telegram delivers a message to `/telegram/webhook` on Cloud Run.
2. Hub creates (or reuses, after link dedupe) an `InboxItem` and runs an isolated ADK session `cap_{item_id}`.
3. The agent calls tools: `save_inbox_item`, `organize_item`, `save_financial_fact`, `propose_calendar_event`, `propose_email`, …
4. Sensitive side effects (Calendar create, Gmail send with CV) wait for Telegram inline confirmation.
5. The dashboard reads Firestore via `/api/inbox`, `/api/finance`, `/api/reports` and lets you edit status/folder.

## Storage

| What | Where |
|------|--------|
| Structured cards | Firestore `inbox` |
| Voice / photos / PDFs | GCS bucket |
| Local fallback | `data/inbox.json` when `HUB_USE_FIRESTORE=false` |
| OAuth token | Secret Manager → mounted at `/app/credentials/token.json` |

## Models

| Role | Model |
|------|--------|
| Main agent | `gemini-3.6-flash` (Vertex, location `global`) |
| Fast filing hint | Gemma (best-effort; skipped on 404) |
| Week video | Veo |
| Week audio theme | Lyria |
