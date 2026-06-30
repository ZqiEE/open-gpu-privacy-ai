param(
  [string]$Server = "http://127.0.0.1:8000",
  [int]$MaxSources = 3,
  [int]$MaxDiscoveryQueries = 5,
  [int]$MaxRecords = 512,
  [int]$MaxSteps = 16,
  [string]$BaseModel = "sshleifer/tiny-gpt2",
  [ValidateSet("lora", "qlora", "transformers")]
  [string]$TrainingBackend = "lora",
  [switch]$AllowLightweightFallback,
  [switch]$NoRequireGpu,
  [switch]$Loop,
  [int]$Interval = 1800,
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (!(Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

if (!$SkipInstall) {
  & $Python -m pip install --upgrade pip
  & $Pip install -r requirements.txt
}

$ArgsList = @(
  "scripts\run_autonomous_source_training.py",
  "--server", $Server,
  "--ledger", "runtime_data\continuous_training_ledger.json",
  "--max-sources", "$MaxSources",
  "--max-discovery-queries", "$MaxDiscoveryQueries",
  "--max-records", "$MaxRecords",
  "--max-steps", "$MaxSteps",
  "--base-model", "$BaseModel",
  "--training-backend", "$TrainingBackend"
)

if ($AllowLightweightFallback) {
  $ArgsList += "--allow-lightweight-fallback"
}

if ($NoRequireGpu) {
  $ArgsList += "--no-require-gpu"
}

if ($Loop) {
  $ArgsList += "--loop"
  $ArgsList += "--interval"
  $ArgsList += "$Interval"
}

& $Python @ArgsList
