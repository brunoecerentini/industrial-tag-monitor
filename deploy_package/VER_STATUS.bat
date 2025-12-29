@echo off
cd /d "%~dp0"
echo.
echo === STATUS DO SERVICO ===
nssm status SeedLossMonitor
echo.
echo === ULTIMAS LINHAS DO LOG ===
powershell -command "if (Test-Path logs\seed_loss_monitor.log) { Get-Content logs\seed_loss_monitor.log -Tail 20 } else { Write-Host 'Log ainda nao existe' }"
echo.
pause

