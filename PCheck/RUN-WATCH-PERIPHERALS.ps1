# Quick launcher script for Watch-Peripherals.ps1
# Double-click this file or run: powershell -ExecutionPolicy Bypass -File RUN-WATCH-PERIPHERALS.ps1

$scriptPath = Join-Path $PSScriptRoot "Watch-Peripherals.ps1"

if (Test-Path $scriptPath) {
    Write-Host "Starting Peripheral Watcher..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    & $scriptPath
} else {
    Write-Host "Error: Watch-Peripherals.ps1 not found!" -ForegroundColor Red
    Write-Host "Expected location: $scriptPath" -ForegroundColor Red
    pause
}

