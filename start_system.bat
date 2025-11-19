@echo off
title OptiLogix Launcher

echo =================================================
echo        Starting OptiLogix System...
echo =================================================
echo.

:: 1. Kill old processes
echo [1/3] Killing old Node.js processes...
taskkill /F /IM node.exe /T >nul 2>&1
echo       Done.
echo.

:: 2. Navigate using Relative Path (The Magic Fix)
echo [2/3] Entering project directory...


cd /d "%~dp0"

:: 进入子文件夹
cd optilogix

:: Double Check
if exist package.json (
    echo       Path Correct: %cd%
) else (
    echo       [ERROR] Cannot find package.json!
    echo       Current Dir: %cd%
    echo.
    echo       Please make sure the folder name is exactly 'optilogix'
    pause
    exit
)
echo.

:: 3. Run npm
echo [3/3] Starting Services...
echo       - Login:  http://localhost:3000
echo       - Admin:  http://localhost:3001
echo       - Driver: http://localhost:3002
echo       - Client: http://localhost:3003
echo =================================================

npm run dev

pause