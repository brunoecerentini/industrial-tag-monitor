@echo off
title Diagnostico de Rede - Seed Loss Monitor
echo.
echo ==========================================
echo      DIAGNOSTICO DE REDE - OPC UA
echo ==========================================
echo.

REM Tenta ler do config.ini se existir
set IP_DEFAULT=10.130.112.61
set PORT_DEFAULT=49320

if exist config.ini (
    for /f "tokens=1,2 delims==" %%a in ('type config.ini ^| findstr "ip ="') do (
        set IP_LIDO=%%b
    )
    for /f "tokens=1,2 delims==" %%a in ('type config.ini ^| findstr "porta ="') do (
        set PORTA_LIDA=%%b
    )
)

REM Limpar espacos
if defined IP_LIDO set IP_DEFAULT=%IP_LIDO: =%
if defined PORTA_LIDA set PORT_DEFAULT=%PORTA_LIDA: =%

echo Configuracao detectada/padrao:
echo IP:   %IP_DEFAULT%
echo Porta: %PORT_DEFAULT%
echo.
set /p IP="Confirma IP (Enter para manter %IP_DEFAULT%): "
if "%IP%"=="" set IP=%IP_DEFAULT%

set /p PORTA="Confirma Porta (Enter para manter %PORT_DEFAULT%): "
if "%PORTA%"=="" set PORTA=%PORT_DEFAULT%

echo.
echo ------------------------------------------
echo 1. TESTE DE PING (Conectividade Basica)
echo ------------------------------------------
ping %IP%
if %errorLevel% neq 0 (
    echo.
    echo [FALHA] Nao foi possivel pingar %IP%. Verifique se o IP esta correto e a maquina ligada.
) else (
    echo [OK] Ping respondeu.
)

echo.
echo ------------------------------------------
echo 2. TESTE DE PORTA (Servico Rodando)
echo ------------------------------------------
echo Testando conexao TCP na porta %PORTA%...
powershell -Command "try { $t = New-Object Net.Sockets.TcpClient; $t.Connect('%IP%', %PORTA%); if ($t.Connected) { Write-Host '[SUCESSO] Porta %PORTA% aberta!' -ForegroundColor Green; $t.Close() } } catch { Write-Host '[FALHA] Nao foi possivel conectar na porta %PORTA%. Motivo: ' $_.Exception.Message -ForegroundColor Red }"

echo.
echo ==========================================
echo ANALISE:
echo.
echo Se o Ping funcionou mas a Porta falhou:
echo  - O KEPServer pode estar parado na maquina %IP%.
echo  - O Firewall do Windows na maquina %IP% pode estar bloqueando a porta %PORTA%.
echo  - O KEPServer pode estar usando uma porta diferente.
echo.
echo Se o Ping falhou:
echo  - O IP esta errado.
echo  - A maquina esta desligada ou desconectada da rede.
echo ==========================================
echo.
pause

