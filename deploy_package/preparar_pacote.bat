@echo off
REM ============================================
REM PREPARA O PACOTE PARA ENVIAR A OUTRA PLANTA
REM Execute ANTES de copiar para outra maquina
REM ============================================

echo.
echo Preparando pacote de deploy...
echo.

set "PACK_DIR=%~dp0"

REM Criar pasta de pacotes offline
if not exist "%PACK_DIR%pacotes_offline" mkdir "%PACK_DIR%pacotes_offline"

REM Baixar pacotes offline (se tiver internet)
echo Baixando pacotes para instalacao offline...
pip download pyodbc -d "%PACK_DIR%pacotes_offline" 2>nul
pip download opcua -d "%PACK_DIR%pacotes_offline" 2>nul
pip download lxml -d "%PACK_DIR%pacotes_offline" 2>nul

REM Criar pasta de logs
if not exist "%PACK_DIR%logs" mkdir "%PACK_DIR%logs"

echo.
echo ============================================
echo PACOTE PRONTO PARA DISTRIBUICAO!
echo ============================================
echo.
echo Conteudo do pacote:
echo.
dir /b "%PACK_DIR%"
echo.
echo Copie toda esta pasta para a nova planta.
echo Na nova maquina, execute instalar.bat como Administrador.
echo.
pause

