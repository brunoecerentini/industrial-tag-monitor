@echo off
REM ============================================
REM INSTALACAO DO SERVICO VIA NSSM
REM Execute como Administrador!
REM ============================================

echo ============================================
echo  INSTALADOR DO SERVICO SEED LOSS MONITOR
echo ============================================
echo.

REM Verificar se está rodando como admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Este script precisa ser executado como Administrador!
    echo Clique com botao direito e selecione "Executar como administrador"
    pause
    exit /b 1
)

REM Configurações
set SERVICE_NAME=SeedLossMonitor
set PROJECT_DIR=%~dp0
set PYTHON_PATH=%PROJECT_DIR%venv\Scripts\python.exe
set SCRIPT_PATH=%PROJECT_DIR%cam_monitor_service.py
set NSSM_PATH=%PROJECT_DIR%nssm.exe

REM Verificar se NSSM existe
if not exist "%NSSM_PATH%" (
    echo [AVISO] NSSM nao encontrado em %NSSM_PATH%
    echo.
    echo Baixe o NSSM de: https://nssm.cc/download
    echo Extraia nssm.exe para: %PROJECT_DIR%
    echo.
    pause
    exit /b 1
)

REM Verificar se Python existe
if not exist "%PYTHON_PATH%" (
    echo [AVISO] Python nao encontrado em %PYTHON_PATH%
    echo Ajuste a variavel PYTHON_PATH no script
    echo.
    REM Tenta usar Python do sistema
    set PYTHON_PATH=python
    echo Usando Python do sistema...
)

echo Configuracoes:
echo   Servico: %SERVICE_NAME%
echo   Diretorio: %PROJECT_DIR%
echo   Python: %PYTHON_PATH%
echo   Script: %SCRIPT_PATH%
echo.

REM Parar e remover serviço existente (se houver)
echo Removendo servico existente (se houver)...
"%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
timeout /t 2 /nobreak >nul

REM Instalar novo serviço
echo.
echo Instalando servico...
"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "%SCRIPT_PATH%"

if %errorLevel% neq 0 (
    echo [ERRO] Falha ao instalar servico!
    pause
    exit /b 1
)

REM Configurar parâmetros do serviço
echo Configurando parametros...

REM Diretório de trabalho
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"

REM Logs de saída
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\service_stdout.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\service_stderr.log"

REM Rotação de logs do NSSM
"%NSSM_PATH%" set %SERVICE_NAME% AppStdoutCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppStderrCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateOnline 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 10485760

REM Reiniciar automaticamente em caso de falha
"%NSSM_PATH%" set %SERVICE_NAME% AppExit Default Restart
"%NSSM_PATH%" set %SERVICE_NAME% AppRestartDelay 30000

REM Descrição do serviço
"%NSSM_PATH%" set %SERVICE_NAME% Description "Monitor de Perda de Sementes ITU - Coleta dados OPC UA e salva no SQL Server"
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "Seed Loss Monitor ITU"

REM Iniciar automaticamente
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Criar diretório de logs
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

echo.
echo ============================================
echo  SERVICO INSTALADO COM SUCESSO!
echo ============================================
echo.
echo Comandos uteis:
echo   Iniciar:  nssm start %SERVICE_NAME%
echo   Parar:    nssm stop %SERVICE_NAME%
echo   Status:   nssm status %SERVICE_NAME%
echo   Remover:  nssm remove %SERVICE_NAME%
echo   Editar:   nssm edit %SERVICE_NAME%
echo.
echo Logs em: %PROJECT_DIR%\logs\
echo.

REM Perguntar se quer iniciar agora
set /p START_NOW="Deseja iniciar o servico agora? (S/N): "
if /i "%START_NOW%"=="S" (
    echo.
    echo Iniciando servico...
    "%NSSM_PATH%" start %SERVICE_NAME%
    timeout /t 3 /nobreak >nul
    "%NSSM_PATH%" status %SERVICE_NAME%
)

echo.
pause


