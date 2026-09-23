@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
pip install -r requirements-integrations.txt

echo.
echo No Google Cloud, confirme que estas APIs estao habilitadas:
echo - Google Calendar API
echo - Gmail API
echo - Google Tasks API
echo.
if not exist "data\google_credentials.json" (
    echo Baixe suas credenciais OAuth Desktop do Google Cloud e salve como:
    echo data\google_credentials.json
)
echo.
echo Depois defina GOOGLE_ENABLED=true no .env.
echo.
echo Os tokens sao separados por servico para nao quebrar autorizações existentes:
echo data\google_token.json          ^(Calendar^)
echo data\google_gmail_token.json    ^(Gmail^)
echo data\google_tasks_token.json    ^(Tasks^)
pause
