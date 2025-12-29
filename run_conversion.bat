@echo off
echo Iniciando conversao...
cd /d "%~dp0"
python taglist_to_deloitte.py
echo.
echo Pressione qualquer tecla para sair...
pause > nul

