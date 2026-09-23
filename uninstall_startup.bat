@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$startup=[Environment]::GetFolderPath('Startup'); $link=Join-Path $startup 'NEXUS.lnk'; if (Test-Path $link) { Remove-Item $link -Force; Write-Host 'Atalhos removidos.' } else { Write-Host 'NEXUS ja nao estava configurado.' }"
pause
