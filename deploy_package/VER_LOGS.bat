@echo off
cd /d "%~dp0"
echo Abrindo logs em tempo real... (Ctrl+C para sair)
echo.
powershell -command "Get-Content logs\seed_loss_monitor.log -Wait -Tail 50"

