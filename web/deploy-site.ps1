# Copy the web terminal's page (web\site) into the web site's folder.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File web\deploy-site.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File web\deploy-site.ps1 -Root D:\mypage\inhahe.com
#
# bbs.html and bbs-local.html go in the site's root folder, and its bbs-term folder is
# made the same as web\site\bbs-term (what is no longer in the project is removed
# there). Nothing else in the site is touched.
param([string]$Root = 'D:\mypage\inhahe.com')
$ErrorActionPreference = 'Stop'

$site = Join-Path $PSScriptRoot 'site'
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw "No web site folder at $Root" }
Copy-Item -LiteralPath (Join-Path $site 'bbs.html'), (Join-Path $site 'bbs-local.html') -Destination $Root -Force
# robocopy /MIR mirrors bbs-term alone; exit codes below 8 mean success
& robocopy (Join-Path $site 'bbs-term') (Join-Path $Root 'bbs-term') /MIR /NJH /NJS /NFL /NDL /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed (exit code $LASTEXITCODE)" }
$global:LASTEXITCODE = 0
"Deployed the web terminal to $Root"
