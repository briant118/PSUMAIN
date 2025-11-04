param(
  [Parameter()][string]$PcName = $env:COMPUTERNAME,
  [Parameter()][string]$Server  = "http://127.0.0.1:8000",
  [Parameter()][int]$IntervalSeconds = 2
)

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "Polling watcher on $PcName -> $Server (every $IntervalSeconds s)"

function Send-Event {
  param([string]$Action,[string]$Id,[string]$Name)
  try {
    Invoke-RestMethod -Method Post -Uri "$Server/ajax/peripheral-event/" -Body @{
      pc_name     = $PcName
      action      = $Action
      device_id   = $Id
      device_name = $Name
    } | Out-Null
    Write-Host "Sent: $Action | $Name | $Id"
  } catch {
    Write-Warning "Send failed: $($_.Exception.Message)"
  }
}

function Get-DeviceSnapshot {
  Get-CimInstance Win32_PnPEntity |
    Where-Object {
      $_.PNPClass -match 'Keyboard|HID|USB|Mouse|MEDIA|AUDIO|MODEM|BLUETOOTH' -or
      $_.PNPDeviceID -like 'USB*'
    } |
    Select-Object @{n='Id';e={$_.PNPDeviceID}}, @{n='Name';e={$_.Name}}
}

# Initial snapshot
$prev = @{}
Get-DeviceSnapshot | ForEach-Object { $prev[$_.Id] = $_.Name }

Write-Host "Watching... (Ctrl+C to stop)"
while ($true) {
  Start-Sleep -Seconds $IntervalSeconds
  $curr = @{}
  Get-DeviceSnapshot | ForEach-Object { $curr[$_.Id] = $_.Name }

  # Added
  foreach ($id in $curr.Keys) {
    if (-not $prev.ContainsKey($id)) {
      $nm = $curr[$id]
      if ([string]::IsNullOrWhiteSpace($nm)) { $nm = 'Unknown Device' }
      Send-Event -Action 'attached' -Id $id -Name $nm
    }
  }
  # Removed
  foreach ($id in $prev.Keys) {
    if (-not $curr.ContainsKey($id)) {
      $nm = $prev[$id]
      if ([string]::IsNullOrWhiteSpace($nm)) { $nm = 'Unknown Device' }
      Send-Event -Action 'removed' -Id $id -Name $nm
    }
  }

  $prev = $curr
}