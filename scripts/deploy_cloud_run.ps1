# Deploy Hub to Cloud Run (dashboard + Telegram webhook).
# Vertex Gemini uses location=global; the Cloud Run service itself stays regional.

$ErrorActionPreference = "Stop"
$gcloud = Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloud)) { $gcloud = "gcloud" }

$Project = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { "gen-lang-client-0614591307" }
$Region = "us-central1"
$Service = "hub"
$Bucket = "hub-media-gen-lang-client-0614591307"
$Secret = "telegram-bot-token"
$OauthToken = "hub-oauth-token"
$Root = Split-Path -Parent $PSScriptRoot
$TokenFile = Join-Path $Root "credentials\token.json"

& $gcloud config set project $Project
& $gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com storage.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com gmail.googleapis.com --project $Project

$ProjectNumber = (& $gcloud projects describe $Project --format="value(projectNumber)").Trim()
$RunSa = "$ProjectNumber-compute@developer.gserviceaccount.com"

& $gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$RunSa" --role="roles/datastore.user" --condition=None --quiet
& $gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$RunSa" --role="roles/storage.objectAdmin" --condition=None --quiet
& $gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$RunSa" --role="roles/aiplatform.user" --condition=None --quiet
& $gcloud secrets add-iam-policy-binding $Secret --member="serviceAccount:$RunSa" --role="roles/secretmanager.secretAccessor" --project $Project --quiet

function Sync-Secret([string]$Name, [string]$File) {
  if (-not (Test-Path $File)) { throw "Missing $File" }
  $prev = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & $gcloud secrets describe $Name --project $Project 2>$null | Out-Null
  $exists = ($LASTEXITCODE -eq 0)
  $ErrorActionPreference = $prev
  if (-not $exists) {
    & $gcloud secrets create $Name --data-file=$File --replication-policy=automatic --project $Project --quiet
  } else {
    & $gcloud secrets versions add $Name --data-file=$File --project $Project --quiet
  }
  & $gcloud secrets add-iam-policy-binding $Name --member="serviceAccount:$RunSa" --role="roles/secretmanager.secretAccessor" --project $Project --quiet
}

Sync-Secret $OauthToken $TokenFile

$EnvVars = @(
  "GOOGLE_GENAI_USE_VERTEXAI=true",
  "GOOGLE_CLOUD_PROJECT=$Project",
  "GOOGLE_CLOUD_LOCATION=global",
  "HUB_USE_FIRESTORE=true",
  "GCS_BUCKET=$Bucket",
  "PYTHONPATH=src"
) -join ","

& $gcloud run deploy $Service `
  --source . `
  --region $Region `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 3 `
  --set-env-vars $EnvVars `
  --set-secrets "TELEGRAM_BOT_TOKEN=${Secret}:latest,/app/credentials/token.json=${OauthToken}:latest" `
  --quiet `
  --project $Project

$url = (& $gcloud run services describe $Service --region $Region --project $Project --format="value(status.url)").Trim()
Write-Host "Cloud Run URL: $url"
Write-Host "Webhook path: $url/telegram/webhook"
