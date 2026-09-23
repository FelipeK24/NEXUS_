@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar as dependencias principais.
    pause
    exit /b 1
)

if not exist ".env" copy ".env.example" ".env"
if not exist "data\memory.json" echo {}>"data\memory.json"
if not exist "data\tasks.json" echo []>"data\tasks.json"
if not exist "data\contacts.json" echo {}>"data\contacts.json"
if not exist "models\piper" mkdir "models\piper"

python -m playwright install chromium
python scripts\download_piper_voice.py

if exist ".env" (
    echo.
    echo Setup concluido.
    echo Configure sua GROQ_API_KEY em .env.
    echo Para Gmail/Calendar, use setup_integrations.bat.
) else (
    echo Falha ao criar .env.
)

pause
