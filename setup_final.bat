@echo off
setlocal
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Instalando navegador Chromium do Playwright...
python -m playwright install chromium
if not exist .env copy .env.example .env
if not exist data\memory.json echo {}> data\memory.json
if not exist data\tasks.json echo []> data\tasks.json
if not exist data\contacts.json echo {}> data\contacts.json
echo.
echo Setup final concluido.
echo Para Google/Gmail/Calendar: execute setup_integrations.bat
pause
