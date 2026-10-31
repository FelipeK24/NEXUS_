@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
pip install -r requirements-integrations.txt
if not exist "data\google_credentials.json" (
    echo.
    echo Baixe suas credenciais OAuth Desktop do Google Cloud e salve como:
    echo data\google_credentials.json
)
echo.
echo Depois defina GOOGLE_ENABLED=true no .env.
pause
