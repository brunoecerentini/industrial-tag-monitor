@echo off
chcp 65001 >nul

REM ============================================
REM TESTE DE CONEXOES - SEED LOSS MONITOR
REM ============================================

title Teste de Conexoes

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           TESTE DE CONEXOES - SEED LOSS MONITOR              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo [1/4] Verificando Python...
python --version
if %errorLevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    goto :fim
)
echo [OK] Python funcionando
echo.

echo [2/4] Verificando pyodbc...
python -c "import pyodbc; print('pyodbc versao:', pyodbc.version)"
if %errorLevel% neq 0 (
    echo [ERRO] pyodbc nao instalado!
    goto :fim
)
echo [OK] pyodbc funcionando
echo.

echo [3/4] Verificando opcua...
python -c "from opcua import Client; print('opcua OK')"
if %errorLevel% neq 0 (
    echo [ERRO] opcua nao instalado!
    goto :fim
)
echo [OK] opcua funcionando
echo.

echo [4/4] Testando script principal...
echo Pressione Ctrl+C para parar apos alguns ciclos
echo.
python "%INSTALL_DIR%\seed_loss_monitor.py"

:fim
echo.
pause

