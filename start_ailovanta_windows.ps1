param(
  [int]$Port = 8000,
  [switch]$SkipInstall,
  [switch]$SkipValidate,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
  param([string]$Name)
  if (!(Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name was not found. Install it first, then run this script again."
  }
}

function Test-PortAvailable {
  param([int]$CandidatePort)
  $Listener = $null
  try {
    $Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $CandidatePort)
    $Listener.Start()
    return $true
  } catch {
    return $false
  } finally {
    if ($null -ne $Listener) {
      $Listener.Stop()
    }
  }
}

function Find-FreePort {
  param([int]$PreferredPort)
  for ($Candidate = $PreferredPort; $Candidate -lt ($PreferredPort + 100); $Candidate++) {
    if (Test-PortAvailable $Candidate) {
      return $Candidate
    }
  }
  throw "No available localhost port found from $PreferredPort to $($PreferredPort + 99)."
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$RequestedPort = $Port
$Port = Find-FreePort $RequestedPort

Write-Host "Ailovanta local launcher"
Write-Host "Project: $Root"
Write-Host "Port:    $Port"
if ($Port -ne $RequestedPort) {
  Write-Host "Note: requested port $RequestedPort was unavailable, using $Port instead." -ForegroundColor Yellow
}

Require-Command python

if (!(Test-Path "requirements.txt")) {
  throw "requirements.txt was not found. Run this script from the Ailovanta repository root."
}

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

New-Item -ItemType Directory -Force -Path "runtime_data" | Out-Null

if (!$SkipValidate) {
  Write-Step "Running project validation"
  & $Python validate.py
}

Write-Step "Bootstrapping local owned runtime"
& $Python scripts\bootstrap_owned_runtime.py

$env:AILOVANTA_PREFER_OWNED_MODEL = "true"

$Url = "http://127.0.0.1:$Port/app"
$DocsUrl = "http://127.0.0.1:$Port/docs"
$DashboardUrl = "http://127.0.0.1:$Port/dashboard"

if (!$NoBrowser) {
  Write-Step "Opening browser"
  Start-Process $Url
}

Write-Step "Starting Ailovanta API"
Write-Host "App:       $Url"
Write-Host "Dashboard: $DashboardUrl"
Write-Host "API Docs:  $DocsUrl"
Write-Host ""
Write-Host "Keep this window open. Press Ctrl+C here to stop Ailovanta."
Write-Host ""

& $Python -m uvicorn api.main:app --host 127.0.0.1 --port $Port --reload
