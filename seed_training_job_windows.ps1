param(
  [string]$Server = "http://127.0.0.1:8000",
  [int]$MaxSteps = 8
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (!(Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python scripts\seed_local_training_job.py --server $Server --max-steps $MaxSteps
