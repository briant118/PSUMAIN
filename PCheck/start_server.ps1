Write-Host "Starting Django server with WebSocket support (Daphne)..." -ForegroundColor Green
Set-Location $PSScriptRoot
$env:DJANGO_SETTINGS_MODULE = "PCheckMain.settings"
python -m daphne -b 127.0.0.1 -p 8000 PCheckMain.asgi:application

