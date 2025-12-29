# Industrial Data Pipeline & Tag Monitor

Este projeto é uma solução robusta para aquisição, monitoramento e persistência de dados industriais (IIoT). Ele atua como um middleware entre chão de fábrica (OPC UA / KepServer) e sistemas corporativos (SQL Server), garantindo integridade de dados e alta disponibilidade.

## 🚀 Funcionalidades Principais

*   **Aquisição OPC UA:** Conexão nativa com servidores OPC UA (ex: KepServerEx) para leitura de tags em tempo real.
*   **Persistência Resiliente:** Gravação em SQL Server com tratamento de falhas de conexão.
*   **Buffer Local (Failover):** Sistema de backup automático em CSV caso o banco de dados esteja indisponível, garantindo zero perda de dados.
*   **Gestão de Recursos:** Monitoramento de memória e limpeza automática de cache para operação contínua 24/7.
*   **Integração Windows Service:** Scripts preparados para execução como serviços Windows (via NSSM) com rotação de logs.
*   **Schema Protection:** Verificação e correção automática de tipos de dados (overflow protection) no banco SQL.

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python 3.10+
*   **Protocolos:** OPC UA (Binary)
*   **Banco de Dados:** Microsoft SQL Server
*   **Bibliotecas Chave:**
    *   `opcua`: Cliente OPC UA assíncrono/síncrono.
    *   `pyodbc`: Conectividade ODBC de alta performance.
    *   `lxml`: Processamento eficiente de dados.

## 📂 Estrutura do Projeto

*   `cam_monitor_service.py`: Script principal do serviço de monitoramento.
*   `create_tag2.py`: Automação para criação em massa de tags no KepServer via API REST/Configuration.
*   `setup_seed_loss.sql`: Scripts DDL para criação da estrutura de banco de dados.
*   `deploy_package/`: Ferramentas para empacotamento e deploy offline em ambiente fabril.

## ⚙️ Instalação e Configuração

1.  **Pré-requisitos:**
    *   Python 3.10 ou superior.
    *   Driver ODBC para SQL Server instalado no sistema.

2.  **Instalação das dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuração do Banco de Dados:**
    Execute o script `setup_seed_loss.sql` no seu servidor SQL para criar a tabela e índices necessários.

4.  **Configuração do Ambiente:**
    Verifique as variáveis de conexão no arquivo `cam_monitor_service.py` ou `config.ini`:
    *   `OPC_URL`: Endpoint do servidor OPC.
    *   `DB_SERVER`: Endereço do SQL Server.

## 📦 Deploy como Serviço

O projeto inclui scripts `.bat` e configurações para deploy automatizado usando NSSM (Non-Sucking Service Manager), ideal para servidores de produção que requerem reinício automático e execução em background.

---
*Desenvolvido para garantir a confiabilidade de dados na indústria 4.0.*

