@echo off
title YouTube Turbo Studio
cd /d "%~dp0"

echo ========================================================
echo  Starting YouTube Turbo Studio...
echo ========================================================

if exist "C:\Program Files\Python312\python.exe" (
    "C:\Program Files\Python312\python.exe" app.py
) else if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" app.py
) else (
    python app.py
)

pause
