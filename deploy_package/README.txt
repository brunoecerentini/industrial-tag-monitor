╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    SEED LOSS MONITOR - GUIA DE IMPLANTACAO                   ║
║                    Sistema de Monitoramento de Perda de Sementes             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
                              CONTEUDO DO PACOTE
================================================================================

  seed_loss_monitor.py   - Script principal do monitor
  config.ini             - Arquivo de configuracao (IPs, portas, etc)
  tags_config.csv        - Lista de tags OPC a monitorar
  instalar.bat           - Instalador interativo
  desinstalar.bat        - Desinstalador do servico
  testar_conexoes.bat    - Teste de conexoes
  nssm.exe               - Gerenciador de servicos Windows
  pacotes_offline/       - Bibliotecas Python para instalacao offline
  logs/                  - Diretorio de logs (criado automaticamente)

================================================================================
                           REQUISITOS DO SISTEMA
================================================================================

  - Windows Server 2012+ ou Windows 10+
  - Python 3.10 ou superior
  - Acesso de rede ao KEPServer (OPC UA)
  - Acesso de rede ao SQL Server
  - Usuario Windows com permissao no SQL Server

================================================================================
                          INSTALACAO PASSO A PASSO
================================================================================

PASSO 1: PREPARAR A MAQUINA
---------------------------
1. Instale Python 3.10+ (adicione ao PATH durante instalacao)
   Download: https://www.python.org/downloads/

2. Copie toda a pasta deploy_package para o servidor:
   Exemplo: C:\Users\USUARIO\Desktop\kepserver_env


PASSO 2: BAIXAR NSSM (se nao incluido)
--------------------------------------
1. Acesse: https://nssm.cc/download
2. Baixe a versao mais recente
3. Extraia nssm.exe para a pasta de instalacao


PASSO 3: CONFIGURAR TAGS
------------------------
1. Edite o arquivo tags_config.csv
2. Adicione as tags OPC que deseja monitorar
3. Formato: uma tag por linha, caminho completo
   Exemplo: ITU_Husker.PLC_Secador_Debulha.Seed_loss_log.SRT1.bER


PASSO 4: INSTALAR (Offline ou Online)
-------------------------------------
OPCAO A - Instalador Interativo:
  1. Clique com botao direito em instalar.bat
  2. Selecione "Executar como administrador"
  3. Siga as instrucoes na tela
  4. Informe IPs, portas, usuario e senha quando solicitado

OPCAO B - Instalacao Manual:
  1. Edite config.ini com as configuracoes corretas
  2. Abra CMD como Administrador
  3. Execute:
     cd C:\CAMINHO\PARA\PASTA
     pip install pacotes_offline\*.whl pacotes_offline\*.tar.gz
     nssm install SeedLossMonitor "python" "C:\CAMINHO\seed_loss_monitor.py"
     nssm set SeedLossMonitor AppDirectory "C:\CAMINHO"
     nssm set SeedLossMonitor ObjectName "DOMINIO\USUARIO" "SENHA"
     nssm start SeedLossMonitor


PASSO 5: VERIFICAR INSTALACAO
-----------------------------
1. Execute: nssm status SeedLossMonitor
   Deve mostrar: SERVICE_RUNNING

2. Verifique os logs:
   type logs\seed_loss_monitor.log

3. Verifique no SQL Server se os dados estao sendo inseridos

================================================================================
                            COMANDOS UTEIS
================================================================================

  Iniciar servico:     nssm start SeedLossMonitor
  Parar servico:       nssm stop SeedLossMonitor
  Reiniciar servico:   nssm restart SeedLossMonitor
  Ver status:          nssm status SeedLossMonitor
  Editar config:       nssm edit SeedLossMonitor
  Remover servico:     nssm remove SeedLossMonitor confirm

  Ver logs em tempo real:
  powershell -command "Get-Content logs\seed_loss_monitor.log -Wait -Tail 50"

================================================================================
                         SOLUCAO DE PROBLEMAS
================================================================================

PROBLEMA: Servico nao inicia (SERVICE_STOPPED)
CAUSA: Geralmente erro de Python ou bibliotecas
SOLUCAO:
  1. Verifique: type logs\service_stderr.log
  2. Teste manualmente: python seed_loss_monitor.py
  3. Verifique se pyodbc e opcua estao instalados


PROBLEMA: Erro de conexao SQL Server
CAUSA: Usuario sem permissao ou servico rodando como SYSTEM
SOLUCAO:
  1. Configure usuario correto:
     nssm set SeedLossMonitor ObjectName "DOMINIO\USUARIO" "SENHA"
  2. Ou: nssm edit SeedLossMonitor -> aba "Log on"


PROBLEMA: Erro de conexao OPC UA
CAUSA: KEPServer nao acessivel ou configuracao incorreta
SOLUCAO:
  1. Teste ping: ping IP_DO_KEPSERVER
  2. Verifique porta: telnet IP_DO_KEPSERVER 49320
  3. Verifique se KEPServer esta rodando


PROBLEMA: Alto uso de memoria
CAUSA: Cache acumulado
SOLUCAO:
  1. O sistema limpa automaticamente a cada hora
  2. Reinicie o servico: nssm restart SeedLossMonitor


PROBLEMA: Dados nao salvam no SQL
CAUSA: Conexao SQL falhou
SOLUCAO:
  1. Dados sao salvos automaticamente em backup_seed_loss.csv
  2. Verifique logs para detalhes do erro
  3. Quando SQL voltar, dados continuam sendo enviados

================================================================================
                            CONFIGURACOES
================================================================================

Arquivo: config.ini

[OPC_UA]
ip = 10.130.106.61          # IP do KEPServer
porta = 49320               # Porta OPC UA
namespace = 2               # Namespace Index

[SQL_SERVER]  
ip = 10.130.254.40          # IP do SQL Server
porta = 1600                # Porta SQL
database = ITU_Seed_Loss    # Nome do banco
tabela = seed_loss          # Nome da tabela

[MONITOR]
intervalo_segundos = 60     # Intervalo de leitura
ciclos_limpeza = 60         # Limpeza a cada N ciclos

[PLANTA]
nome_planta = ITU           # Identificacao da planta

================================================================================
                              CONTATO
================================================================================

Logs principais:
  - logs\seed_loss_monitor.log  (log do monitor)
  - logs\service_stdout.log     (saida do servico)
  - logs\service_stderr.log     (erros do servico)

Backup quando SQL offline:
  - backup_seed_loss.csv

================================================================================

