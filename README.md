# Industrial Data Pipeline & Tag Automation

Este repositório contém ferramentas para automação industrial, divididas em dois módulos principais: monitoramento de dados (OT -> IT) e automação de engenharia (criação de tags).

## 📂 Estrutura do Projeto

### 1. `monitor_service/` (Serviço de Coleta)
Serviço crítico para execução 24/7 em chão de fábrica.
*   **Função:** Coleta dados via OPC UA e persiste no SQL Server.
*   **Destaques:** Proteção contra perda de dados (buffer local CSV), limpeza automática de cache e integração com serviços Windows.
*   **Portas:** Usa porta OPC UA (default: 49320) e SQL Server (1433/1600).

### 2. `tag_automation/` (Engenharia)
Ferramentas para ganho de produtividade na configuração do SCADA/OPC.
*   **Função:** Criação em massa de tags no KepServerEX via API REST.
*   **Destaques:** Converte listas CSV/Excel em configuração de tags, economizando horas de trabalho manual.
*   **Portas:** Usa porta HTTP/REST do KepServer (default: 57412).

### 3. `utils/`
Scripts auxiliares e testes.

## 🚀 Como Usar

### Instalação Geral
```bash
pip install -r requirements.txt
```

### Para rodar o Monitoramento
1.  Configure as variáveis no arquivo `monitor_service/cam_monitor_service.py` ou `config.ini`.
2.  Instale como serviço usando os scripts na pasta `monitor_service/`.

### Para criar Tags
1.  Edite sua lista de tags em `tag_automation/taglist.csv`.
2.  Execute:
    ```bash
    python tag_automation/create_tag2.py
    ```

---
*Organizado para escalabilidade e manutenção.*
