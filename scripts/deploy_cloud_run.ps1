# Deploy Hub to Cloud Run (dashboard + Telegram webhook), sized to stay in the GCP free tier.
# Gemini runs on Vertex (pay per use, near zero at current volume); Gemma/Veo/Lyria are off.

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
& $gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$RunSa" --role="roles/aiplatform.user" --condition=None --quiet
& $gcloud storage buckets add-iam-policy-binding "gs://$Bucket" --member="serviceAccount:$RunSa" --role="roles/storage.objectAdmin" --project $Project --quiet
& $gcloud secrets add-iam-policy-binding $Secret --member="serviceAccount:$RunSa" --role="roles/secretmanager.secretAccessor" --project $Project --quiet

function Secret-Exists([string]$Name) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & $gcloud secrets describe $Name --project $Project 2>$null | Out-Null
  $exists = ($LASTEXITCODE -eq 0)
  $ErrorActionPreference = $prev
  return $exists
}

# Secret Manager is free up to 6 active versions in total. Keep only the newest one per secret.
function Prune-SecretVersions([string]$Name) {
  $versions = @(& $gcloud secrets versions list $Name --project $Project --filter="state!=DESTROYED" --sort-by="~createTime" --format="value(name)")
  foreach ($v in ($versions | Select-Object -Skip 1)) {
    & $gcloud secrets versions destroy $v --secret $Name --project $Project --quiet | Out-Null
  }
}

function Sync-Secret([string]$Name, [string]$File) {
  if (-not (Test-Path $File)) { throw "Missing $File" }
  if (-not (Secret-Exists $Name)) {
    & $gcloud secrets create $Name --data-file=$File --replication-policy=automatic --project $Project --quiet
  } else {
    # Only add a version when the content changed; every version costs once past the free tier.
    $current = (& $gcloud secrets versions access latest --secret $Name --project $Project) -join "`n"
    if (($current -replace "`r", "").Trim() -ne ((Get-Content $File -Raw) -replace "`r", "").Trim()) {
      & $gcloud secrets versions add $Name --data-file=$File --project $Project --quiet
    }
  }
  & $gcloud secrets add-iam-policy-binding $Name --member="serviceAccount:$RunSa" --role="roles/secretmanager.secretAccessor" --project $Project --quiet
}

Sync-Secret $OauthToken $TokenFile

function Ensure-RandomSecret([string]$Name, [int]$Bytes = 24, [switch]$PrintOnce) {
  if (Secret-Exists $Name) {
    & $gcloud secrets add-iam-policy-binding $Name --member="serviceAccount:$RunSa" --role="roles/secretmanager.secretAccessor" --project $Project --quiet
    return
  }
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $buf = New-Object byte[] $Bytes
  $rng.GetBytes($buf)
  $value = [Convert]::ToBase64String($buf).TrimEnd("=").Replace("+", "-").Replace("/", "_")
  $tmp = Join-Path $env:TEMP "$Name.txt"
  Set-Content -Path $tmp -Value $value -NoNewline -Encoding ascii
  & $gcloud secrets create $Name --data-file=$tmp --replication-policy=automatic --project $Project --quiet
  Remove-Item $tmp -Force
  & $gcloud secrets add-iam-policy-binding $Name --member="serviceAccount:$RunSa" --role="roles/secretmanager.secretAccessor" --project $Project --quiet
  if ($PrintOnce) {
    Write-Host ""
    Write-Host "HUB ACCESS CODE (save it; shown only when the secret is created):"
    Write-Host $value
    Write-Host ""
  }
}

Ensure-RandomSecret "hub-session-secret" -Bytes 32
Ensure-RandomSecret "hub-access-code" -Bytes 18 -PrintOnce

foreach ($name in @($Secret, $OauthToken, "hub-session-secret", "hub-access-code", "hub-oauth-client")) {
  Prune-SecretVersions $name
}

# Writable private app. Telegram webhook stays public; dashboard needs the access code.
$ReadOnly = if ($env:HUB_READ_ONLY) { $env:HUB_READ_ONLY } else { "false" }
$EnvVars = @(
  "GOOGLE_GENAI_USE_VERTEXAI=true",
  "GOOGLE_CLOUD_PROJECT=$Project",
  "GOOGLE_CLOUD_LOCATION=global",
  "HUB_USE_FIRESTORE=true",
  "GCS_BUCKET=$Bucket",
  "HUB_READ_ONLY=$ReadOnly",
  "HUB_REQUIRE_AUTH=true",
  "HUB_OWNER_EMAIL=vilson.dj97@gmail.com",
  "PYTHONPATH=src"
) -join ","

# max-instances=1 made Cloud Run answer 429 while recycling the only instance.
& $gcloud run deploy $Service `
  --source . `
  --region $Region `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --no-cpu-boost `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 3 `
  --set-env-vars $EnvVars `
  --set-secrets "TELEGRAM_BOT_TOKEN=${Secret}:latest,HUB_ACCESS_CODE=hub-access-code:latest,HUB_SESSION_SECRET=hub-session-secret:latest,/app/credentials/token.json=${OauthToken}:latest" `
  --quiet `
  --project $Project

$url = (& $gcloud run services describe $Service --region $Region --project $Project --format="value(status.url)").Trim()
Write-Host "Cloud Run URL: $url"
Write-Host "Webhook path: $url/telegram/webhook"
