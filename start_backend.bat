@echo off
echo Starting Cerina Backend Server...
echo Server will run on http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.

cd /d "C:\Cerina_Foundry_ver0"
set PYTHONPATH=C:\Cerina_Foundry_ver0
uvicorn backend.server:app --reload --port 8000
pause
