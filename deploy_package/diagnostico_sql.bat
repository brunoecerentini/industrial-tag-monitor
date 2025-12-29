@echo off
title Diagnostico SQL Server - Seed Loss Monitor
echo.
echo ==========================================
echo      DIAGNOSTICO DE CONEXAO SQL SERVER
echo ==========================================
echo.

REM Valores padrao baseados no seu log
set IP_SQL=10.130.254.210
set PORTA_SQL=1600

if exist config.ini (
    for /f "tokens=1,2 delims==" %%a in ('type config.ini ^| findstr /C:"ip ="') do (
        REM Precisamos filtrar para pegar o IP do SQL, nao do OPC
        REM Mas como e script bat simples, vamos assumir os valores do log por enquanto ou pedir input
    )
)

echo Configuração detectada (do log):
echo IP SQL:    %IP_SQL%
echo Porta SQL: %PORTA_SQL%
echo.
set /p IP_SQL="Confirma IP (Enter para manter %IP_SQL%): "
if "%IP_SQL%"=="" set IP_SQL=10.130.254.210

set /p PORTA_SQL="Confirma Porta (Enter para manter %PORTA_SQL%): "
if "%PORTA_SQL%"=="" set PORTA_SQL=1600

echo.
echo ------------------------------------------
echo 1. TESTE DE REDE (Ping)
echo ------------------------------------------
ping %IP_SQL%
if %errorLevel% neq 0 (
    echo [FALHA] Nao foi possivel pingar o servidor SQL %IP_SQL%.
    echo Verifique se o IP esta correto e a maquina ligada.
) else (
    echo [OK] Servidor responde ao Ping.
)

echo.
echo ------------------------------------------
echo 2. TESTE DE PORTA (TCP)
echo ------------------------------------------
echo Testando porta %PORTA_SQL% no IP %IP_SQL%...
powershell -Command "try { $t = New-Object Net.Sockets.TcpClient; $t.Connect('%IP_SQL%', %PORTA_SQL%); if ($t.Connected) { Write-Host '[SUCESSO] Porta %PORTA_SQL% aberta!' -ForegroundColor Green; $t.Close() } } catch { Write-Host '[FALHA] Nao foi possivel conectar na porta %PORTA_SQL%.' -ForegroundColor Red; Write-Host 'Erro: ' $_.Exception.Message }"

echo.
echo ------------------------------------------
echo 3. TESTE DE DRIVERS ODBC
echo ------------------------------------------
echo Listando drivers ODBC instalados...
powershell -Command "Get-OdbcDriver | Format-Table Name, Platform -AutoSize"

echo.
echo ==========================================
echo ANALISE:
echo.
echo Se o teste de Porta (2) FALHOU:
echo  - O Firewall no servidor SQL (%IP_SQL%) esta bloqueando a porta %PORTA_SQL%.
echo  - O SQL Server nao esta configurado para ouvir na porta %PORTA_SQL%.
echo  - O servico SQL Server pode estar parado.
echo.
echo Se o teste de Porta (2) FUNCIONOU, mas o Python falha:
echo  - Pode ser problema de autenticacao (Usuario/Senha).
echo  - Pode ser falta do driver ODBC correto.
echo.
pause

