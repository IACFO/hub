# Hub — Inbox-to-Life

Agente pessoal multimodal para o [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/). Voce despeja audio, foto, boleto, link ou texto no Telegram. O agente (Google ADK + Gemini 3.6 Flash) organiza, extrai acoes e grava no Google Calendar / Drive depois da confirmacao.

Trilha: **Taskmaster**.

## Rodar local (depois do setup)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python scripts/check_setup.py
python -m hub.telegram_bot
```

Dashboard: `python -m hub.server` e abra http://localhost:8080

ADK web (debug do agente): `adk web --port 8000` na pasta `agents/`

Passo a passo do que **voce** precisa ligar (Telegram, Cloud Console, OAuth, creditos): [docs/SETUP.md](docs/SETUP.md)

## Stack

- Gemini 3.6 Flash via **Vertex AI** (creditos GCP); AI Studio so como fallback
- Google ADK (agente + tools)
- Telegram (captura)
- Google Calendar + Drive + Gmail (acao com confirmacao)
- Firestore + Cloud Storage + Cloud Run (deploy: `scripts/deploy_cloud_run.ps1`)
- Gemma (arquivista), Veo (recap da semana), Lyria (tema da Agenda da semana)
- Fallback local JSON enquanto Firestore/GCS nao estao ligados no `.env`
