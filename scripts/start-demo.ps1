# Starts the full LP Diligence Agent demo: backend, frontend, and Cloudflare tunnel.
# Opens three PowerShell windows so you can see each process's output.
#
# Usage: from the repo root or anywhere, run:
#   .\scripts\start-demo.ps1
#
# Stop everything by closing the three windows (or Ctrl+C in each).

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repo "backend"
$frontend = Join-Path $repo "frontend"

if (-not (Test-Path (Join-Path $backend ".venv\Scripts\Activate.ps1"))) {
    Write-Error "Backend venv not found at $backend\.venv. Run 'python -m venv .venv' in backend\ first."
}
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Error "Frontend node_modules not found at $frontend. Run 'npm install' in frontend\ first."
}

function Start-PSWindow {
    param(
        [string]$Title,
        [string]$WorkingDir,
        [string]$Command
    )
    # -NoExit keeps the window open after the command finishes (or errors)
    # so you can read the output.
    $args = @(
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkingDir'; $Command"
    )
    Start-Process powershell.exe -ArgumentList $args
}

Write-Host "Starting backend (port 8000)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "LP Diligence - Backend (:8000)" `
    -WorkingDir $backend `
    -Command ".\.venv\Scripts\Activate.ps1; uvicorn lp_diligence.api:app --port 8000"

# Wait a moment so backend logs start scrolling before the next window opens.
Start-Sleep -Seconds 2

Write-Host "Starting frontend (port 3003)..." -ForegroundColor Cyan
Start-PSWindow `
    -Title "LP Diligence - Frontend (:3003)" `
    -WorkingDir $frontend `
    -Command "npm run dev"

Start-Sleep -Seconds 4

Write-Host "Starting Cloudflare named tunnel (lp-diligence.krawczun.com)..." -ForegroundColor Cyan
$configPath = Join-Path $PSScriptRoot "cloudflared-config.yml"
Start-PSWindow `
    -Title "LP Diligence - Tunnel" `
    -WorkingDir $repo `
    -Command "cloudflared tunnel --config '$configPath' run lp-diligence"

Write-Host ""
Write-Host "All three windows launched." -ForegroundColor Green
Write-Host "  - Backend logs:  'LP Diligence - Backend' window"
Write-Host "  - Frontend logs: 'LP Diligence - Frontend' window"
Write-Host "  - Tunnel logs:   'LP Diligence - Tunnel' window"
Write-Host ""
Write-Host "Local URL:  http://localhost:3003"
Write-Host "Public URL: https://lp-diligence.krawczun.com"
