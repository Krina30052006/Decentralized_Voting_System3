@echo off
setlocal
cd /d "%~dp0"

echo Stopping Decentralized Voting local stack...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" stop_local_stack.py
) else (
    py -3 stop_local_stack.py
)

echo.
if errorlevel 1 (
    echo Stop command finished with warnings.
) else (
    echo Stop command completed.
)

pause
endlocal
