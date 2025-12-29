@echo off
REM ============================================
REM SEED LOSS MONITOR - SCRIPT DE EXECUCAO
REM Para uso com NSSM ou Task Scheduler
REM ============================================

REM Configurar diretório de trabalho
cd /d "C:\Users\whs913\Desktop\kepserver_env"

REM Ativar ambiente virtual (se existir)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Executar o script Python
python cam_monitor_service.py

REM Se o script terminar, aguardar antes de reiniciar
timeout /t 10 /nobreak


