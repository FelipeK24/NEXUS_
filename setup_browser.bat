@echo off
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
python -m playwright install chromium
if errorlevel 1 (
    echo.
    echo Falha ao instalar o Chromium do Playwright.
    pause
    exit /b 1
)
echo.
echo Chromium do NEXUS instalado com sucesso.
pause
