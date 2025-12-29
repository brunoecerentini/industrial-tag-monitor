@echo off
REM ============================================
REM LIMPEZA DE CACHE E LOGS
REM Pode ser agendado para rodar semanalmente
REM ============================================

echo ============================================
echo  LIMPEZA DE CACHE - SEED LOSS MONITOR
echo ============================================
echo.

set PROJECT_DIR=%~dp0
set LOG_DIR=%PROJECT_DIR%\logs
set DIAS_MANTER=30

echo Diretorio: %PROJECT_DIR%
echo Logs: %LOG_DIR%
echo Manter arquivos dos ultimos %DIAS_MANTER% dias
echo.

REM Limpar arquivos de log antigos
echo Limpando logs antigos...
forfiles /p "%LOG_DIR%" /s /m *.log /d -%DIAS_MANTER% /c "cmd /c del @path" 2>nul
if %errorLevel% equ 0 (
    echo   Logs antigos removidos
) else (
    echo   Nenhum log antigo encontrado
)

REM Limpar arquivos __pycache__
echo Limpando cache Python...
for /d /r "%PROJECT_DIR%" %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d"
        echo   Removido: %%d
    )
)

REM Limpar arquivos .pyc
del /s /q "%PROJECT_DIR%\*.pyc" 2>nul

REM Limpar backups CSV muito grandes (> 100MB) mais antigos que 30 dias
echo Verificando backups CSV antigos...
forfiles /p "%PROJECT_DIR%" /m backup_*.csv /d -%DIAS_MANTER% /c "cmd /c del @path" 2>nul

REM Limpar arquivos temporários do Windows
echo Limpando temp do sistema...
del /q /f "%TEMP%\*.tmp" 2>nul

echo.
echo ============================================
echo  LIMPEZA CONCLUIDA!
echo ============================================
echo.

REM Se executado manualmente, pausar
if "%1"=="" pause


