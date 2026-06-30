param(
  [string]$Server = "http://127.0.0.1:8000",
  [int]$ContributionPercent = 90,
  [int]$Interval = 10,
  [switch]$Once,
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (!(Test-Path ".venv\Scripts\python.exe")) {
  Write-Step "Creating Python virtual environment"
  python -m venv .venv
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

if (!$SkipInstall) {
  Write-Step "Installing dependencies"
  & $Python -m pip install --upgrade pip
  & $Pip install -r requirements.txt
}

Write-Step "Probing local GPU"
& $Python scripts\show_gpu.py

Write-Step "Starting local training worker"
Write-Host "Server: $Server"
Write-Host "Contribution: $ContributionPercent%"
Write-Host "Keep this window open. Press Ctrl+C here to stop the worker."
Write-Host ""

$ArgsList = @(
  "scripts\run_node.py",
  "--server", $Server,
  "--enable-gpu",
  "--contribution-percent", "$ContributionPercent",
  "--interval", "$Interval"
)

if ($Once) {
  $ArgsList += "--once"
}

& $Python @ArgsList
