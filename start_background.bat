@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo .venv nao encontrado.
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "main.py" --tray
