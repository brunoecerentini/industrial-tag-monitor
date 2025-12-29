@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================
REM INSTALADOR SEED LOSS MONITOR
REM Versao para multiplas plantas industriais
REM ============================================

title Instalador Seed Loss Monitor

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         INSTALADOR - SEED LOSS MONITOR                       ║
echo ║         Sistema de Monitoramento de Perda de Sementes        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Verificar se está rodando como admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Este instalador precisa ser executado como Administrador!
    echo.
    echo Clique com botao direito em instalar.bat e selecione:
    echo "Executar como administrador"
    echo.
    pause
    exit /b 1
)

REM Definir diretório atual
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo Diretorio de instalacao: %INSTALL_DIR%
echo.

REM ============================================
REM COLETAR INFORMACOES
REM ============================================

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    CONFIGURACAO DA PLANTA                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set /p NOME_PLANTA="Nome da Planta (ex: ITU, UBERLANDIA): "
if "%NOME_PLANTA%"=="" set NOME_PLANTA=PLANTA

echo.
echo --- Configuracao OPC UA (KEPServer) ---
set /p OPC_IP="IP do KEPServer [10.130.106.61]: "
if "%OPC_IP%"=="" set OPC_IP=10.130.106.61

set /p OPC_PORTA="Porta OPC UA [49320]: "
if "%OPC_PORTA%"=="" set OPC_PORTA=49320

echo.
echo --- Configuracao SQL Server ---
set /p SQL_IP="IP do SQL Server [10.130.254.40]: "
if "%SQL_IP%"=="" set SQL_IP=10.130.254.40

set /p SQL_PORTA="Porta SQL Server [1600]: "
if "%SQL_PORTA%"=="" set SQL_PORTA=1600

set /p SQL_DATABASE="Nome do Banco [ITU_Seed_Loss]: "
if "%SQL_DATABASE%"=="" set SQL_DATABASE=ITU_Seed_Loss

set /p DB_TEM_ESPACO="O nome do banco comeca com espaco? (S/N) [N]: "
if /i "%DB_TEM_ESPACO%"=="S" (
    set SQL_DATABASE= %SQL_DATABASE%
    echo   [INFO] Banco sera salvo como: " %SQL_DATABASE%"
)

set /p SQL_TABELA="Nome da Tabela [seed_loss]: "
if "%SQL_TABELA%"=="" set SQL_TABELA=seed_loss

echo.
echo --- Configuracao do Servico Windows ---
set /p NOME_SERVICO="Nome do Servico [SeedLossMonitor]: "
if "%NOME_SERVICO%"=="" set NOME_SERVICO=SeedLossMonitor

set /p USUARIO_WINDOWS="Usuario Windows (dominio\usuario): "
if "%USUARIO_WINDOWS%"=="" (
    echo [AVISO] Usuario nao informado. O servico rodara como SYSTEM.
    set USUARIO_WINDOWS=
)

if not "%USUARIO_WINDOWS%"=="" (
    echo.
    echo Digite a senha do usuario %USUARIO_WINDOWS%:
    set /p SENHA_WINDOWS="Senha: "
)

echo.
echo --- Configuracao do Monitor ---
set /p INTERVALO="Intervalo de leitura em segundos [60]: "
if "%INTERVALO%"=="" set INTERVALO=60

REM ============================================
REM CONFIRMAR CONFIGURACOES
REM ============================================

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  CONFIRME AS CONFIGURACOES                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo   Planta:        %NOME_PLANTA%
echo   OPC UA:        %OPC_IP%:%OPC_PORTA%
echo   SQL Server:    %SQL_IP%:%SQL_PORTA%
echo   Database:      %SQL_DATABASE%
echo   Tabela:        %SQL_TABELA%
echo   Servico:       %NOME_SERVICO%
echo   Usuario:       %USUARIO_WINDOWS%
echo   Intervalo:     %INTERVALO% segundos
echo.

set /p CONFIRMA="As configuracoes estao corretas? (S/N): "
if /i not "%CONFIRMA%"=="S" (
    echo.
    echo Instalacao cancelada. Execute novamente para reconfigurar.
    pause
    exit /b 0
)

REM ============================================
REM GERAR ARQUIVO DE CONFIGURACAO
REM ============================================

echo.
echo Gerando arquivo de configuracao...

REM Preparar nome do banco (com aspas se tiver espaco)
if /i "%DB_TEM_ESPACO%"=="S" (
    set DB_CONFIG_LINE=database = "%SQL_DATABASE%"
) else (
    set DB_CONFIG_LINE=database = %SQL_DATABASE%
)

REM Escrever config.ini linha por linha
echo # ============================================> "%INSTALL_DIR%\config.ini"
echo # CONFIGURACAO DO SEED LOSS MONITOR>> "%INSTALL_DIR%\config.ini"
echo # Gerado em: %date% %time%>> "%INSTALL_DIR%\config.ini"
echo # Planta: %NOME_PLANTA%>> "%INSTALL_DIR%\config.ini"
echo # ============================================>> "%INSTALL_DIR%\config.ini"
echo.>> "%INSTALL_DIR%\config.ini"
echo [OPC_UA]>> "%INSTALL_DIR%\config.ini"
echo ip = %OPC_IP%>> "%INSTALL_DIR%\config.ini"
echo porta = %OPC_PORTA%>> "%INSTALL_DIR%\config.ini"
echo namespace = 2>> "%INSTALL_DIR%\config.ini"
echo.>> "%INSTALL_DIR%\config.ini"
echo [SQL_SERVER]>> "%INSTALL_DIR%\config.ini"
echo ip = %SQL_IP%>> "%INSTALL_DIR%\config.ini"
echo porta = %SQL_PORTA%>> "%INSTALL_DIR%\config.ini"
echo %DB_CONFIG_LINE%>> "%INSTALL_DIR%\config.ini"
echo tabela = %SQL_TABELA%>> "%INSTALL_DIR%\config.ini"
echo.>> "%INSTALL_DIR%\config.ini"
echo [SERVICO]>> "%INSTALL_DIR%\config.ini"
echo nome_servico = %NOME_SERVICO%>> "%INSTALL_DIR%\config.ini"
echo usuario = %USUARIO_WINDOWS%>> "%INSTALL_DIR%\config.ini"
echo senha = >> "%INSTALL_DIR%\config.ini"
echo.>> "%INSTALL_DIR%\config.ini"
echo [MONITOR]>> "%INSTALL_DIR%\config.ini"
echo intervalo_segundos = %INTERVALO%>> "%INSTALL_DIR%\config.ini"
echo ciclos_limpeza = 60>> "%INSTALL_DIR%\config.ini"
echo.>> "%INSTALL_DIR%\config.ini"
echo [PLANTA]>> "%INSTALL_DIR%\config.ini"
echo nome_planta = %NOME_PLANTA%>> "%INSTALL_DIR%\config.ini"
echo descricao = Planta %NOME_PLANTA% - Monitoramento Seed Loss>> "%INSTALL_DIR%\config.ini"

echo [OK] Arquivo config.ini criado

REM ============================================
REM VERIFICAR PYTHON
REM ============================================

echo.
echo Verificando Python...

where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.10+ e adicione ao PATH
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('where python') do (
    set "PYTHON_PATH=%%i"
    goto :found_python
)
:found_python

echo [OK] Python encontrado: %PYTHON_PATH%

REM ============================================
REM VERIFICAR DEPENDENCIAS
REM ============================================

echo.
echo Verificando dependencias...

REM Tentar instalacao offline se disponivel
if exist "%INSTALL_DIR%\pacotes_offline\*.whl" (
    echo [INFO] Instalando pacotes offline...
    pip install --no-index --find-links="%INSTALL_DIR%\pacotes_offline" pyodbc opcua lxml python-dateutil pytz six
) else (
    echo [INFO] Pacotes offline nao encontrados. Verificando instalacao...
    
    python -c "import pyodbc" >nul 2>&1
    if !errorLevel! neq 0 (
        echo [INFO] Instalando pyodbc...
        pip install pyodbc
    )

    python -c "from opcua import Client" >nul 2>&1
    if !errorLevel! neq 0 (
        echo [INFO] Instalando opcua...
        pip install opcua
    )
)

REM Verificacao final
python -c "import pyodbc" >nul 2>&1
if !errorLevel! neq 0 echo [ERRO] Falha na instalacao do pyodbc!

python -c "from opcua import Client" >nul 2>&1
if !errorLevel! neq 0 echo [ERRO] Falha na instalacao do opcua!

echo [OK] Dependencias verificadas

REM ============================================
REM CRIAR DIRETORIOS
REM ============================================

echo.
echo Criando diretorios...

if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
echo [OK] Diretorio de logs criado

REM ============================================
REM VERIFICAR NSSM
REM ============================================

echo.
echo Verificando NSSM...

if not exist "%INSTALL_DIR%\nssm.exe" (
    echo [ERRO] nssm.exe nao encontrado em %INSTALL_DIR%
    echo.
    echo Baixe o NSSM de: https://nssm.cc/download
    echo Extraia nssm.exe para: %INSTALL_DIR%
    echo.
    pause
    exit /b 1
)

echo [OK] NSSM encontrado

REM ============================================
REM INSTALAR SERVICO
REM ============================================

echo.
echo Instalando servico Windows...

REM Remover servico existente (se houver)
"%INSTALL_DIR%\nssm.exe" stop %NOME_SERVICO% >nul 2>&1
"%INSTALL_DIR%\nssm.exe" remove %NOME_SERVICO% confirm >nul 2>&1
timeout /t 2 /nobreak >nul

REM Instalar servico
"%INSTALL_DIR%\nssm.exe" install %NOME_SERVICO% "%PYTHON_PATH%" "%INSTALL_DIR%\seed_loss_monitor.py"

if %errorLevel% neq 0 (
    echo [ERRO] Falha ao instalar servico!
    pause
    exit /b 1
)

REM Configurar servico
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppDirectory "%INSTALL_DIR%"
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppStdout "%INSTALL_DIR%\logs\service_stdout.log"
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppStderr "%INSTALL_DIR%\logs\service_stderr.log"
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppStdoutCreationDisposition 4
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppStderrCreationDisposition 4
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppRotateFiles 1
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppRotateOnline 1
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppRotateBytes 10485760
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppExit Default Restart
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% AppRestartDelay 30000
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% Description "Seed Loss Monitor - %NOME_PLANTA%"
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% DisplayName "Seed Loss Monitor - %NOME_PLANTA%"
"%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% Start SERVICE_AUTO_START

REM Configurar usuario (se informado)
if not "%USUARIO_WINDOWS%"=="" (
    echo Configurando usuario do servico...
    "%INSTALL_DIR%\nssm.exe" set %NOME_SERVICO% ObjectName "%USUARIO_WINDOWS%" "%SENHA_WINDOWS%"
)

echo [OK] Servico instalado

REM ============================================
REM TESTAR E INICIAR
REM ============================================

echo.
set /p INICIAR="Deseja iniciar o servico agora? (S/N): "
if /i "%INICIAR%"=="S" (
    echo.
    echo Iniciando servico...
    "%INSTALL_DIR%\nssm.exe" start %NOME_SERVICO%
    timeout /t 3 /nobreak >nul
    "%INSTALL_DIR%\nssm.exe" status %NOME_SERVICO%
)

REM ============================================
REM FINALIZAR
REM ============================================

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              INSTALACAO CONCLUIDA COM SUCESSO!               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Comandos uteis:
echo   Iniciar:    nssm start %NOME_SERVICO%
echo   Parar:      nssm stop %NOME_SERVICO%
echo   Status:     nssm status %NOME_SERVICO%
echo   Reiniciar:  nssm restart %NOME_SERVICO%
echo   Remover:    nssm remove %NOME_SERVICO%
echo.
echo Logs em: %INSTALL_DIR%\logs\
echo Config:  %INSTALL_DIR%\config.ini
echo.

pause

