@echo off
REM Decentralized Voting System - Startup Script
REM This batch file starts all required services: Hardhat node, contract deployment, and Flask backend

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo.
echo ========================================================
echo    DECENTRALIZED VOTING SYSTEM - STARTUP
echo ========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.13+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Check if Node.js/npm is installed
npx --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js/npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Node.js detected
echo.

echo Starting Decentralized Voting System...
echo.

REM Run the main startup script
python start_local_stack.py
set STARTUP_RESULT=%errorlevel%

if %STARTUP_RESULT% equ 0 (
    echo.
    echo ========================================================
    echo    [SUCCESS] SYSTEM STARTED SUCCESSFULLY
    echo ========================================================
    echo.
    echo Web Interface: http://127.0.0.1:5000
    echo.
    echo Services Running:
    echo   - Hardhat Node:      http://127.0.0.1:8545
    echo   - Flask Backend:     http://127.0.0.1:5000
    echo.
    echo Voter Portal:         http://127.0.0.1:5000/login.html
    echo Admin Portal:         http://127.0.0.1:5000/admin_login.html
    echo.
    echo Logs:
    echo   - Node:    .runtime/hardhat-node.log
    echo   - Backend: .runtime/backend.log
    echo.
    
    REM Open the web interface in default browser
    echo Opening web interface in browser...
    timeout /t 2 /nobreak
    start http://127.0.0.1:5000
    
    echo.
    echo Keep this window open while using the system
    echo Press Ctrl+C to stop all services
    echo.
    
    REM Keep the window open
    pause
) else (
    echo.
    echo ========================================================
    echo    [ERROR] STARTUP FAILED
    echo ========================================================
    echo.
    echo Please check the error messages above and try again.
    echo For support, check:
    echo   - .runtime/backend.log
    echo   - .runtime/hardhat-node.log
    echo.
    pause
    exit /b 1
)

endlocal
