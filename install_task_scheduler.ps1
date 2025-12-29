# ============================================
# INSTALACAO VIA TASK SCHEDULER (PowerShell)
# Execute como Administrador!
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " INSTALADOR TASK SCHEDULER - SEED LOSS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está rodando como admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERRO] Execute este script como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botao direito no PowerShell e selecione 'Executar como administrador'" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Configurações
$TaskName = "SeedLossMonitor"
$ProjectDir = "C:\Users\whs913\Desktop\kepserver_env"
$PythonPath = "C:\Users\whs913\Desktop\kepserver_env\venv\Scripts\python.exe"
$ScriptPath = "C:\Users\whs913\Desktop\kepserver_env\cam_monitor_service.py"

# Verificar se Python existe, senão usar do sistema
if (-not (Test-Path $PythonPath)) {
    Write-Host "[AVISO] Python venv nao encontrado, usando python do sistema" -ForegroundColor Yellow
    $PythonPath = "python"
}

Write-Host "Configuracoes:" -ForegroundColor Green
Write-Host "  Task: $TaskName"
Write-Host "  Diretorio: $ProjectDir"
Write-Host "  Python: $PythonPath"
Write-Host "  Script: $ScriptPath"
Write-Host ""

# Remover tarefa existente (se houver)
Write-Host "Removendo tarefa existente (se houver)..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Criar diretório de logs
$LogDir = Join-Path $ProjectDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "Diretorio de logs criado: $LogDir" -ForegroundColor Green
}

# Configurar a ação (executar Python com o script)
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectDir

# Trigger: Iniciar no boot do sistema
$TriggerBoot = New-ScheduledTaskTrigger -AtStartup

# Trigger: Iniciar no logon (backup)
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn

# Configurações da tarefa
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 9999) `
    -MultipleInstances IgnoreNew

# Principal (rodar como SYSTEM para não depender de login)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Registrar a tarefa
Write-Host ""
Write-Host "Registrando tarefa agendada..." -ForegroundColor Yellow

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $TriggerBoot `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Monitor de Perda de Sementes ITU - Coleta dados OPC UA e salva no SQL Server" `
        -Force

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host " TAREFA CRIADA COM SUCESSO!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Comandos uteis (PowerShell):" -ForegroundColor Cyan
    Write-Host "  Iniciar:  Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Parar:    Stop-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Status:   Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
    Write-Host "  Remover:  Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "Ou via CMD:" -ForegroundColor Cyan
    Write-Host "  Iniciar:  schtasks /run /tn '$TaskName'"
    Write-Host "  Parar:    schtasks /end /tn '$TaskName'"
    Write-Host "  Status:   schtasks /query /tn '$TaskName'"
    Write-Host ""
    
    # Perguntar se quer iniciar agora
    $startNow = Read-Host "Deseja iniciar a tarefa agora? (S/N)"
    if ($startNow -eq "S" -or $startNow -eq "s") {
        Write-Host ""
        Write-Host "Iniciando tarefa..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 3
        
        $taskInfo = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
        Write-Host "Status: $($taskInfo.LastTaskResult)" -ForegroundColor Green
    }
}
catch {
    Write-Host "[ERRO] Falha ao criar tarefa: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Pressione Enter para sair"


