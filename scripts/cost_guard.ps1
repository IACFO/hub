# One-off cost cleanup: old container images, a keep-2 cleanup policy, and a budget alert.
# Needs an OPEN billing account linked to the project.

param([int]$BudgetBRL = 5)

$ErrorActionPreference = "Stop"
$gcloud = Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloud)) { $gcloud = "gcloud" }

$Project = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { "gen-lang-client-0614591307" }

# Artifact Registry is free up to 0.5 GB. Every `run deploy --source` pushes a new image.
$policy = Join-Path $env:TEMP "hub-ar-cleanup.json"
@'
[
  {"name": "keep-2-recent", "action": {"type": "Keep"}, "mostRecentVersions": {"keepCount": 2}},
  {"name": "delete-old", "action": {"type": "Delete"}, "condition": {"tagState": "any", "olderThan": "1d"}}
]
'@ | Set-Content -Path $policy -Encoding ascii

# gcloud writes progress notes to stderr, which PowerShell 5.1 turns into terminating errors under Stop.
$ErrorActionPreference = "Continue"
$repos = @((& $gcloud artifacts repositories list --project $Project --format=json 2>$null | Out-String | ConvertFrom-Json) |
  Where-Object { $_.format -eq "DOCKER" })
foreach ($repo in $repos) {
  # name = projects/<p>/locations/<loc>/repositories/<repo>
  $parts = $repo.name.Split("/")
  $location = $parts[3]
  $repoId = $parts[5]
  & $gcloud artifacts repositories set-cleanup-policies $repoId --location $location --project $Project --policy $policy --no-dry-run --quiet

  $base = "$location-docker.pkg.dev/$Project/$repoId"
  $images = @(& $gcloud artifacts docker images list $base --format="value(package)" | Sort-Object -Unique)
  foreach ($image in $images) {
    $digests = @(& $gcloud artifacts docker images list $image --sort-by="~UPDATE_TIME" --format="value(version)")
    foreach ($digest in ($digests | Select-Object -Skip 1)) {
      Write-Host "Deleting $image@$digest"
      & $gcloud artifacts docker images delete "$image@$digest" --delete-tags --quiet
    }
  }
}
Remove-Item $policy -Force
$ErrorActionPreference = "Stop"

# Budget alert: e-mails billing admins at 50%, 90% and 100%. It alerts; it does not cap spend.
$account = ((& $gcloud billing projects describe $Project --format="value(billingAccountName)").Trim()).Replace("billingAccounts/", "")
& $gcloud services enable billingbudgets.googleapis.com --project $Project
$existing = @(& $gcloud billing budgets list --billing-account $account --filter="displayName='Hub - limite mensal'" --format="value(name)")
if ($existing.Count -eq 0) {
  & $gcloud billing budgets create `
    --billing-account $account `
    --display-name "Hub - limite mensal" `
    --budget-amount "${BudgetBRL}BRL" `
    --filter-projects "projects/$Project" `
    --threshold-rule percent=0.5 `
    --threshold-rule percent=0.9 `
    --threshold-rule percent=1.0
} else {
  Write-Host "Budget already exists: $($existing[0])"
}
