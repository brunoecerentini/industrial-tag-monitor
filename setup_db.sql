-- 1. Criação do Banco de Dados (se não existir)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'MonitoramentoOPC')
BEGIN
    CREATE DATABASE MonitoramentoOPC;
END
GO

USE MonitoramentoOPC;
GO

-- 2. Criação da Tabela de Leituras
-- Observação: Se você adicionar novas tags no CSV, precisará adicionar colunas aqui com:
-- ALTER TABLE LeiturasTags ADD nome_da_nova_tag FLOAT;

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[LeiturasTags]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[LeiturasTags](
        [Id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [DataHora] [datetime] DEFAULT GETDATE(),
        
        -- Colunas baseadas no seu tags_config.csv atual
        [final_cam_without_husk] [float] NULL,
        [final_cam_with_husk] [float] NULL,
        [final_cam_total] [float] NULL,
        [final_cam_status] [float] NULL
    );
END
GO

-- Apenas para verificação
SELECT TOP 10 * FROM LeiturasTags ORDER BY DataHora DESC;

