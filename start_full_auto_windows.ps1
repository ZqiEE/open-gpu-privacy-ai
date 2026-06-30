param(
  [int]$Port = 8000,
  [int]$MaxSources = 3,
  [int]$MaxDiscoveryQueries = 5,
  [int]$MaxRecords = 512,
  [int]$MaxSteps = 16,
  [string]$BaseModel = "sshleifer/tiny-gpt2",
  [ValidateSet("lora", "qlora", "transformers")]
  [string]$TrainingBackend = "lora",
  [switch]$AllowLightweightFallback,
  [switch]$NoRequireGpu,
  [int]$AutoInterval = 1800,
  [int]$WorkerInterval = 10,
  [int]$ReplicaInterval = 60,
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

function Wait-HttpOk {
  param([string]$Url, [int]$Seconds = 45)
  $Deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $Deadline) {
    try {
      Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 3 | Out-Null
      return
    } catch {
      Start-Sleep -Seconds 1
    }
  }
  throw "Timed out waiting for $Url"
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
  throw "python was not found. Install Python first, then run this script again."
}

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

Write-Step "Bootstrapping owned runtime"
& $Python scripts\bootstrap_owned_runtime.py | Out-Host

$ResolvedPort = Find-FreePort $Port
$Server = "http://127.0.0.1:$ResolvedPort"
$AppUrl = "$Server/app"

$Env:AILOVANTA_PREFER_OWNED_MODEL = "true"

Write-Step "Starting API service"
$ApiArgs = @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$ResolvedPort")
$ApiProcess = Start-Process -FilePath $Python -ArgumentList $ApiArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden
Wait-HttpOk "$Server/health"

Write-Step "Starting autonomous discovery/training queue"
$AutoArgs = @(
  "scripts\run_autonomous_source_training.py",
  "--server", $Server,
  "--ledger", "runtime_data\continuous_training_ledger.json",
  "--max-sources", "$MaxSources",
  "--max-discovery-queries", "$MaxDiscoveryQueries",
  "--max-records", "$MaxRecords",
  "--max-steps", "$MaxSteps",
  "--base-model", "$BaseModel",
  "--training-backend", "$TrainingBackend",
  "--loop",
  "--interval", "$AutoInterval"
)
if ($AllowLightweightFallback) {
  $AutoArgs += "--allow-lightweight-fallback"
}
if ($NoRequireGpu) {
  $AutoArgs += "--no-require-gpu"
}
$AutoProcess = Start-Process -FilePath $Python -ArgumentList $AutoArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden

Write-Step "Starting local GPU/CPU training worker"
$WorkerArgs = @(
  "-m", "api.node_client",
  "--server", $Server,
  "--enable-gpu",
  "--contribution-percent", "90",
  "--interval", "$WorkerInterval"
)
$WorkerProcess = Start-Process -FilePath $Python -ArgumentList $WorkerArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden

Write-Step "Starting replica maintenance loop"
$ReplicaArgs = @(
  "scripts\run_replica_maintenance.py",
  "--loop",
  "--interval", "$ReplicaInterval"
)
$ReplicaProcess = Start-Process -FilePath $Python -ArgumentList $ReplicaArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden

$State = @{
  ok = $true
  server = $Server
  app = $AppUrl
  dashboard = "$Server/dashboard"
  docs = "$Server/docs"
  api_pid = $ApiProcess.Id
  auto_training_pid = $AutoProcess.Id
  worker_pid = $WorkerProcess.Id
  replica_maintenance_pid = $ReplicaProcess.Id
  max_sources = $MaxSources
  max_discovery_queries = $MaxDiscoveryQueries
  max_records = $MaxRecords
  max_steps = $MaxSteps
  base_model = $BaseModel
  training_backend = $TrainingBackend
  require_gpu = !$NoRequireGpu
  allow_lightweight_fallback = [bool]$AllowLightweightFallback
  replica_interval = $ReplicaInterval
  started_at = (Get-Date).ToString("s")
}
$StatePath = Join-Path $Root "runtime_data\full_auto_state.json"
$State | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $StatePath

if (!$NoBrowser) {
  Start-Process $AppUrl
}

Write-Host ""
Write-Host "Ailovanta full-auto is running." -ForegroundColor Green
Write-Host "App:       $AppUrl"
Write-Host "Dashboard: $Server/dashboard"
Write-Host "API Docs:  $Server/docs"
Write-Host "State:     $StatePath"
Write-Host ""
Write-Host "Processes:"
Write-Host "API:       $($ApiProcess.Id)"
Write-Host "AutoTrain: $($AutoProcess.Id)"
Write-Host "Worker:    $($WorkerProcess.Id)"
Write-Host "Replicas:  $($ReplicaProcess.Id)"
Write-Host ""
Write-Host "Press Ctrl+C to stop all full-auto processes."

try {
  $StopRequested = $false
  while ($true) {
    Start-Sleep -Seconds 5
    foreach ($Process in @($ApiProcess, $AutoProcess, $WorkerProcess, $ReplicaProcess)) {
      if ($Process.HasExited) {
        Write-Host "A full-auto child process exited: PID=$($Process.Id)"
        $StopRequested = $true
        break
      }
    }
    if ($StopRequested) {
      break
    }
  }
} finally {
  Write-Step "Stopping full-auto processes"
  foreach ($Process in @($ReplicaProcess, $WorkerProcess, $AutoProcess, $ApiProcess)) {
    try {
      if ($Process -and !$Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
      }
    } catch {
    }
  }
}
