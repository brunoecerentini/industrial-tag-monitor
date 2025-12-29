@echo off
cd /d "%~dp0"
nssm stop SeedLossMonitor
nssm status SeedLossMonitor
pause

