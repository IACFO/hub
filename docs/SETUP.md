# O que voce precisa fazer (conectores, MCP, Cloud)

Eu ja deixei o codigo pronto para Telegram + ADK + Calendar/Drive. Sem o que esta abaixo, o bot ate funciona (organiza localmente), mas **nao escreve no Google Calendar** e **nao sobe no Cloud Run**.

Faca na ordem. Marque mentalmente: **voce** vs ja esta no repo.

Projeto GCP: `gen-lang-client-0614591307`  
Prazo do video/repo: **31/08 17:00 PT (21:00 BRT)**  
Form dos US$150: **28/08 12:00 PT**

---

## 0. Agora, 5 minutos — creditos do hackathon

1. Abra https://allthingsagentichackathon.devpost.com/resources
2. Preencha o form de **US$150 Google Cloud credits** (tambem: https://forms.gle/riGhgDSHkHeMx8Ca6)
3. Use a mesma conta Google do projeto `gen-lang-client-0614591307`
4. Analise leva ate 72h. Nao espere o credito para comecar o bot.

---

## 1. Telegram bot (obrigatorio para testar hoje)

1. No Telegram, abra [@BotFather](https://t.me/BotFather)
2. Envie `/newbot`
3. Nome visivel: `Hub` (ou o que preferir)
4. Username: algo como `vilson_hub_bot` (tem que terminar com `bot`)
5. Copie o token (`123456:AA...`)
6. No arquivo `.env` desta pasta, adicione (sem aspas):

```
TELEGRAM_BOT_TOKEN=cole_o_token_aqui
GOOGLE_API_KEY=cole_a_mesma_chave_GEMINI_API_KEY
GOOGLE_CLOUD_PROJECT=gen-lang-client-0614591307
```

A chave Gemini que voce ja tem no `.env` vale. O ADK procura `GOOGLE_API_KEY`; o codigo copia de `GEMINI_API_KEY` se a outra estiver vazia, mas o mais simples e duplicar o valor.

7. Me avise quando colar o token. Aí rodamos o bot.

Nada de webhook ainda. Local usa **polling**.

---

## 2. Google Cloud SDK (ainda nao esta nesta maquina)

O `gcloud` nao esta instalado no Windows. Instale:

```powershell
winget install Google.CloudSDK
```

Feche e reabra o terminal, depois:

```powershell
gcloud init
gcloud config set project gen-lang-client-0614591307
gcloud auth application-default login
```

No `gcloud init`, escolha a conta que ja tem as 19 APIs e o projeto `gen-lang-client-0614591307`.

---

## 3. Ligar APIs no Cloud Console (voce clica)

Console: https://console.cloud.google.com/apis/library?project=gen-lang-client-0614591307

Ligue estas (search + Enable):

**Para o demo de acao (fazer hoje / amanha)**

- Google Calendar API
- Google Drive API
- Generative Language API (se ainda nao estiver)

**Quando for usar Firestore / GCS / Cloud Run (credito ou free tier)**

- Cloud Firestore API
- Cloud Storage API
- Cloud Run API
- Cloud Tasks API (depois, digest async)

**Workspace MCP (so depois do OAuth funcionar; nao bloqueia o MVP)**

- `calendarmcp.googleapis.com`
- `drivemcp.googleapis.com`
- `gmailmcp.googleapis.com`
- `workspacemcp.googleapis.com`

Pelo CLI, depois do passo 2:

```powershell
gcloud services enable calendar-json.googleapis.com drive.googleapis.com generativelanguage.googleapis.com
```

MCP (opcional, dia 3+):

```powershell
gcloud services enable calendarmcp.googleapis.com drivemcp.googleapis.com gmailmcp.googleapis.com workspacemcp.googleapis.com
```

---

## 4. OAuth Calendar + Drive (o passo que mais trava)

Sem isso o agente **propoe** o evento, mas o botao "Confirmar" so grava no Hub local.

Conta pessoal (Gmail) **nao** pode usar Audience = Internal. Tem que ser External + test user.

### 4.1 Tela de consentimento

1. https://console.cloud.google.com/auth/overview?project=gen-lang-client-0614591307
   (ou APIs e servicos → Tela de consentimento OAuth)
2. User type: **External**
3. App name: `Hub`
4. User support email e developer contact: seu Gmail
5. Em Data Access / Scopes, adicione:
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/drive.file`
6. Em Audience, **add test user**: o mesmo Gmail que voce usa no Calendar
7. Publishing status: **Testing** (nao precisa publicar o app)

### 4.2 Client ID tipo Desktop

1. https://console.cloud.google.com/auth/clients?project=gen-lang-client-0614591307
2. Create credentials → OAuth client ID → **Desktop app**
3. Nome: `Hub local`
4. Download JSON
5. Salve o arquivo exatamente em:

`credentials/client_secret.json`

(a pasta `credentials/` ja esta no `.gitignore`)

### 4.3 Login local (eu rodo com voce)

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
python scripts/auth_workspace.py
```

O browser abre. Aceite. O token vai para `credentials/token.json`.

Se nao vier refresh token: https://myaccount.google.com/permissions → revogue Hub → rode o script de novo.

Quando isso passar, o botao **Confirmar** no Telegram cria o evento de verdade no Calendar. Esse e o momento do video.

---

## 5. Workspace MCP — o que e, e quando ligar

MCP e o conector oficial Google (Calendar/Drive/Gmail como *tools* do ADK). O hackathon gosta. **Nao e bloqueante para o MVP**: o codigo ja cria eventos pela Calendar API classica, que e mais previsivel.

Ligue MCP so depois dos passos 3 e 4 funcionarem:

1. Enable as APIs `*mcp.googleapis.com` (passo 3)
2. No `.env`: `ENABLE_WORKSPACE_MCP=true`
3. Reinicie o bot

Se o MCP falhar, o agente continua com as tools locais. Nao precisa de nenhum token extra alem do OAuth do passo 4.

Gmail compose e Chat MCP **nao** entram no dia 1. Calendar + Drive bastam para o video.

---

## 6. Firestore, Storage, Cloud Run (quando o credito cair)

Ainda **nao** precisa. O Hub grava em `data/inbox.json` e `data/media/`.

Quando o credito entrar:

1. Crie um database Firestore (Native mode) na mesma regiao, ex. `southamerica-east1`
2. Crie um bucket: `hub-media-gen-lang-client-0614591307`
3. No `.env`:

```
HUB_USE_FIRESTORE=true
GCS_BUCKET=hub-media-gen-lang-client-0614591307
```

4. Cloud Run fica para o dia do deploy (Dockerfile ja esta no repo, escuta `0.0.0.0:$PORT`)

Nao deixe Cloud Run com min instances > 0. Scale to zero.

---

## 7. GitHub

Pasta local ainda nao tinha git. O link `github.com/IACFO/hub` estava 404.

Quando for criar (voce, no GitHub):

1. New repository: `IACFO/hub`, **publico** (jurado precisa ver)
2. Nao suba `.env`, `credentials/`, `data/`
3. Me peca o commit inicial que eu faco o `git init` + primeiro commit + instrucoes de push

Instale tambem o GitHub CLI se quiser que eu suba: `winget install GitHub.cli`

---

## 8. Conferir se esta tudo ligado

```powershell
$env:PYTHONPATH = "src"
python scripts/check_setup.py
```

| Item | Quem faz | Bloqueia o bot local? |
|---|---|---|
| `GEMINI_API_KEY` | ja esta no `.env` | sim |
| `TELEGRAM_BOT_TOKEN` | voce, BotFather | sim |
| OAuth `client_secret.json` + `auth_workspace.py` | voce | nao (so Calendar real) |
| APIs Calendar/Drive | voce no Console | nao (so Calendar real) |
| MCP | depois | nao |
| Firestore/GCS/Cloud Run | credito | nao |
| Form US$150 | voce, ate 28/08 | nao para o codigo; sim para o deploy |

---

## 9. Me mande quando terminar cada bloco

Responda neste chat com:

1. Token do BotFather colado no `.env` (nao cole o token aqui)
2. Print ou "APIs Calendar e Drive enabled"
3. `credentials/client_secret.json` no lugar
4. Form de credito enviado, sim/nao

Aí eu subo o bot, testo o fluxo audio → proposta → confirmar, e seguimos para o dashboard e o Cloud Run.
