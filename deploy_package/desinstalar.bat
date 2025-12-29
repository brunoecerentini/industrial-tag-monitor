@echo off
chcp 65001 >nul

REM ============================================
REM DESINSTALADOR SEED LOSS MONITOR
REM ============================================

title Desinstalador Seed Loss Monitor

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║        DESINSTALADOR - SEED LOSS MONITOR                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Verificar se está rodando como admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Execute como Administrador!
    pause
    exit /b 1
)

set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

set /p NOME_SERVICO="Nome do servico a remover [SeedLossMonitor]: "
if "%NOME_SERVICO%"=="" set NOME_SERVICO=SeedLossMonitor

echo.
echo Parando servico %NOME_SERVICO%...
"%INSTALL_DIR%\nssm.exe" stop %NOME_SERVICO%

echo.
echo Removendo servico %NOME_SERVICO%...
"%INSTALL_DIR%\nssm.exe" remove %NOME_SERVICO% confirm

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              SERVICO REMOVIDO COM SUCESSO!                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Os arquivos de configuracao e logs foram mantidos em:
echo %INSTALL_DIR%
echo.
echo Para remover completamente, delete a pasta manualmente.
echo.

pause

