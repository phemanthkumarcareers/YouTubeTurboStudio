# YouTube Turbo Studio - PowerShell Launcher
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " 🎬  YouTube Turbo Studio Launcher" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$pythonExe = "python"
if (Test-Path "C:\Program Files\Python312\python.exe") {
    $pythonExe = "C:\Program Files\Python312\python.exe"
} elseif (Test-Path "..\.venv\Scripts\python.exe") {
    $pythonExe = "..\.venv\Scripts\python.exe"
}

Write-Host "Launching Studio with $pythonExe..." -ForegroundColor Green
& $pythonExe app.py
