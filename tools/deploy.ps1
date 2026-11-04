# Publish ONE client's site to Cloudflare Pages (Windows PowerShell).  HUMAN ONLY: agents must never run this.
# Usage: .\tools\deploy.ps1 <client-slug>      (set $env:SKIP_BUILD = "1" to reuse the existing dist\)
# Same steps as tools/deploy.sh: build -> approval preflight (digest-bound) -> y/N -> wrangler -> consume.
param([Parameter(Mandatory = $true)][string]$Slug)
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Site = Join-Path $Root "clients\$Slug\site"
Set-Location $Root

if (-not (Test-Path $Site)) { Write-Error "REFUSED: $Site does not exist"; exit 1 }

if ($env:SKIP_BUILD -ne "1") {
  Push-Location $Site
  npm ci --no-audit --no-fund; if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
  npm run build; if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
  Pop-Location
}

$Preflight = uv run python tools/site_release.py preflight $Slug
if ($LASTEXITCODE -ne 0) {
  $Preflight | ForEach-Object { Write-Host $_ }
  Write-Host "REFUSED: no valid site_deploy approval for this exact build. Nothing was published."
  exit 1
}
$Preflight | ForEach-Object { Write-Host $_ }
function Get-Value($Key) { ($Preflight | Where-Object { $_ -like "$Key=*" }) -replace "^$Key=", "" }
$Approval = Get-Value "APPROVAL"
$Project = Get-Value "PROJECT"
$Digest = Get-Value "DIGEST"

Write-Host ""
Write-Host "About to publish:"
Write-Host "  folder   : $Site\dist"
Write-Host "  digest   : $Digest"
Write-Host "  project  : $Project (Cloudflare Pages, production branch main)"
Write-Host "  approval : $Approval"
$Answer = Read-Host "Publish now? [y/N]"
if ($Answer -ne "y" -and $Answer -ne "Y") { Write-Host "Cancelled. Nothing was published."; exit 1 }

npx --yes wrangler pages deploy (Join-Path $Site "dist") --project-name $Project --branch main
if ($LASTEXITCODE -ne 0) { exit 1 }
$By = if ($env:OPERATOR) { $env:OPERATOR } else { "operator" }
uv run python tools/site_release.py consume $Slug $Approval --by $By
Write-Host "Done. Next: point the GBP website link at the right page (with UTM) and submit the sitemap in Search Console."
