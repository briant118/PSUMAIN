@echo off
echo Starting Django server with WebSocket support (Daphne)...
cd /d %~dp0
set DJANGO_SETTINGS_MODULE=PCheckMain.settings
python -m daphne -b 127.0.0.1 -p 8000 PCheckMain.asgi:application

