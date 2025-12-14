@echo off
echo Restarting Cerina Foundry Backend Server...
echo.
echo Press Ctrl+C to stop the server when done
echo.

cd /d "C:\Cerina_Foundry_ver0\backend"
uvicorn server:app --reload --port 8000
