@echo off
setlocal
cd /d "%~dp0"

echo Starting Decentralized Voting local stack...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" start_local_stack.py
) else (
    py -3 start_local_stack.py
)

echo.
if errorlevel 1 (
    echo Startup failed. Check .runtime\backend.log and .runtime\hardhat-node.log
) else (
    echo Startup completed successfully.
)

pause
endlocal
