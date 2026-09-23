@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo .venv nao encontrado.
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $startup=[Environment]::GetFolderPath('Startup'); $link=$ws.CreateShortcut((Join-Path $startup 'NEXUS.lnk')); $link.TargetPath=(Join-Path '%~dp0' '.venv\Scripts\pythonw.exe'); $link.Arguments=('"' + (Join-Path '%~dp0' 'main.py') + '" --tray'); $link.WorkingDirectory='%~dp0'; $link.WindowStyle=7; $link.IconLocation=(Join-Path '%~dp0' 'assets\nexus.ico'); $link.Description='NEXUS - assistente pessoal'; $link.Save()"

echo NEXUS configurado para iniciar com o Windows na bandeja.
pause
