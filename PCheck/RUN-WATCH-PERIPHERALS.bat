@echo off
echo Starting Peripheral Watcher...
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "Watch-Peripherals.ps1"
pause

