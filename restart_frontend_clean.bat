@echo off
echo Cleaning and restarting frontend...
echo.

cd /d "C:\Cerina_Foundry_ver0\frontend"

echo [1/4] Stopping any running dev servers...
timeout /t 2 /nobreak >nul

echo [2/4] Clearing Vite cache...
if exist "node_modules\.vite" (
    rmdir /s /q "node_modules\.vite"
    echo Cache cleared!
) else (
    echo No cache found.
)

echo [3/4] Clearing dist folder...
if exist "dist" (
    rmdir /s /q "dist"
)

echo [4/4] Starting dev server...
echo.
echo The server will start now. After it says "ready", do:
echo 1. Go to your browser
echo 2. Press Ctrl+Shift+R to hard refresh
echo 3. Try Start Foundry again
echo.

npm run dev
