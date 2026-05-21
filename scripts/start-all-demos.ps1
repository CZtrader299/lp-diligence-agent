# Launches both portfolio demos with one command.
#
#   LP Diligence Agent (lp-diligence.krawczun.com):
#     - Backend on :8000   (uvicorn)
#     - Frontend on :3003  (Next.js)
#     - Cloudflare tunnel  (named tunnel: lp-diligence)
#
#   AI Capex Flow (aicapex.krawczun.com):
#     - Frontend on :3001  (Next.js)
#     - Cloudflare tunnel  (named tunnel: ai-capex-flow)
#
# Opens 5 PowerShell windows in total. Stop everything by closing the windows
# (or Ctrl+C in each).
#
# Usage:
#   .\scripts\start-all-demos.ps1

$ErrorActionPreference = "Stop"

$lpRepo = Split-Path -Parent $PSScriptRoot
$lpBackend = Join-Path $lpRepo "backend"
$lpFrontend = Join-Path $lpRepo "frontend"
$lpTunnelConfig = Join-Path $PSScriptRoot "cloudflared-config.yml"

$capexRepo = "C:\Users\krawc\projects\ai-capex-flow"

# --- Sanity checks --------------------------------------------------------

if (-not (Test-Path (Join-Path $lpBackend ".venv\Scripts\Activate.ps1"))) {
    Write-Error "LP Diligence backend venv missing at $lpBackend\.venv"
}
if (-not (Test-Path (Join-Path $lpFrontend "node_modules"))) {
    Write-Error "LP Diligence frontend node_modules missing. Run 'npm install' in $lpFrontend"
}
if (-not (Test-Path (Join-Path $capexRepo "node_modules"))) {
    Write-Error "AI Capex Flow node_modules missing. Run 'npm install' in $capexRepo"
}
if (-not (Test-Path $lpTunnelConfig)) {
    Write-Error "LP Diligence tunnel config missing at $lpTunnelConfig"
}

# --- Helper ---------------------------------------------------------------

function Start-PSWindow {
    param(
        [string]$Title,
        [string]$WorkingDir,
        [string]$Command
    )
    $args = @(
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkingDir'; $Command"
    )
    Start-Process powershell.exe -ArgumentList $args
}

# --- LP Diligence ---------------------------------------------------------

Write-Host "Starting LP Diligence backend (port 8000)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "LP Diligence - Backend (:8000)" `
    -WorkingDir $lpBackend `
    -Command ".\.venv\Scripts\Activate.ps1; uvicorn lp_diligence.api:app --port 8000"

Start-Sleep -Seconds 2

Write-Host "Starting LP Diligence frontend (port 3003)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "LP Diligence - Frontend (:3003)" `
    -WorkingDir $lpFrontend `
    -Command "npm run dev"

Start-Sleep -Seconds 3

Write-Host "Starting LP Diligence tunnel (lp-diligence.krawczun.com)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "LP Diligence - Tunnel" `
    -WorkingDir $lpRepo `
    -Command "cloudflared tunnel --config '$lpTunnelConfig' run lp-diligence"

# --- AI Capex Flow --------------------------------------------------------

Start-Sleep -Seconds 2

Write-Host "Starting AI Capex Flow frontend (port 3001)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "AI Capex - Frontend (:3001)" `
    -WorkingDir $capexRepo `
    -Command "npm run dev"

Start-Sleep -Seconds 3

Write-Host "Starting AI Capex Flow tunnel (aicapex.krawczun.com)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "AI Capex - Tunnel" `
    -WorkingDir $capexRepo `
    -Command "npm run tunnel"

# --- Summary --------------------------------------------------------------

Write-Host ""
Write-Host "All 5 windows launched." -ForegroundColor Green
Write-Host ""
Write-Host "LP Diligence:"
Write-Host "  Local:  http://localhost:3003"
Write-Host "  Public: https://lp-diligence.krawczun.com"
Write-Host ""
Write-Host "AI Capex Flow:"
Write-Host "  Local:  http://localhost:3001"
Write-Host "  Public: https://aicapex.krawczun.com"
