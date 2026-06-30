$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $Root "runtime_data\full_auto_state.json"

if (!(Test-Path $StatePath)) {
  Write-Host "No full-auto state file found: $StatePath"
  exit 0
}

$State = Get-Content $StatePath -Raw | ConvertFrom-Json
$Pids = @($State.replica_maintenance_pid, $State.worker_pid, $State.auto_training_pid, $State.api_pid) | Where-Object { $_ }

foreach ($PidValue in $Pids) {
  try {
    Stop-Process -Id $PidValue -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID $PidValue"
  } catch {
    Write-Host "Could not stop PID $PidValue"
  }
}

Write-Host "Full-auto stop requested."
