@echo off
cd /d "%~dp0"
nssm start SeedLossMonitor
nssm status SeedLossMonitor
pause

