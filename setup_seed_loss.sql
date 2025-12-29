-- =============================================================
-- Script de Criação da Tabela seed_loss
-- Banco: ITU_Seed_Loss
-- Dados recebidos minuto a minuto do OPC UA (KEPServer)
-- =============================================================

-- 1. DELETAR BANCO EXISTENTE (CUIDADO: APAGA TODOS OS DADOS!)
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'ITU_Seed_Loss')
BEGIN
    -- Fecha todas as conexões ativas
    ALTER DATABASE ITU_Seed_Loss SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE ITU_Seed_Loss;
    PRINT '🗑️ Banco ITU_Seed_Loss deletado com sucesso.';
END
GO

-- 2. Criação do Banco de Dados
CREATE DATABASE ITU_Seed_Loss;
PRINT '✅ Banco ITU_Seed_Loss criado.';
GO

USE ITU_Seed_Loss;
GO

-- 3. Criação da Tabela seed_loss
CREATE TABLE [dbo].[seed_loss](
    [Id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [DataHora] [datetime] DEFAULT GETDATE(),
    [linha] [nvarchar](10) NULL,                    -- Identificação da linha (A, B ou C)
    [scale_ticket] [nvarchar](100) NULL,            -- Identificador do lote
    
    -- ========== Campos de Status ==========
    [bER] [bit] NULL,                               -- Erro de leitura
    [bSTATUS] [bit] NULL,                           -- Leitura OK
    [dStatus] [int] NULL,                           -- Status do bloco
    
    -- ========== Leituras Instantâneas - Espigas ==========
    [dInstHuskEars] [int] NULL,                     -- Leitura instantânea espigas com palha
    [dInstNoHuskEars] [int] NULL,                   -- Leitura instantânea espigas sem palha
    [dInstTotalEars] [int] NULL,                    -- Total instantâneo espigas
    [rInstAveHusk] [float] NULL,                    -- Média Instantânea % Espigas com palha
    [rInstAveNoHusk] [float] NULL,                  -- Média Instantânea % Espigas sem palha
    
    -- ========== Leituras Instantâneas - Área/Kernels (NOVAS) ==========
    [rInstHasKernels] [float] NULL,                 -- Leitura instantânea área com sementes
    [rInstKernels] [float] NULL,                    -- Leitura instantânea área com sementes soltas
    [rInstNoKernels] [float] NULL,                  -- Leitura instantânea área sem sementes
    [rInstSeedLoss] [float] NULL,                   -- % Instantâneo de perdas de sementes
    
    -- ========== Dados da Amostra (Sample) ==========
    [dTotHuskSample] [int] NULL,                    -- Total de espigas com palha da amostra
    [dTotNoHuskSample] [int] NULL,                  -- Total de espigas sem palha da amostra
    [dTotEarsSample] [int] NULL,                    -- Total de espigas da amostra
    [dSampleTime] [int] NULL,                       -- Tempo de amostragem
    [rTotAveHuskSample] [float] NULL,               -- Média % espigas com palha na amostra
    [rTotAveNoHuskSample] [float] NULL,             -- Média % de espigas sem palha da amostra
    [rTotAveHasKernelsSample] [float] NULL,         -- Média % área granada da amostra
    [rTotAveNoKernelsSample] [float] NULL,          -- Média % área degranada da amostra
    [rTotAveKernelsSample] [float] NULL,            -- Média % sementes soltas da amostra
    
    -- ========== Dados do Lote (Batch / Scale Ticket) ==========
    [dTotHuskBatch] [int] NULL,                     -- Total de espigas com palha no lote
    [dTotNoHuskBatch] [int] NULL,                   -- Total de espigas sem palha no lote
    [dTotEarsBatch] [int] NULL,                     -- Total de espigas no lote
    [dBatchTime] [int] NULL,                        -- Tempo do lote
    [rTotAveHuskBatch] [float] NULL,                -- Média % de espigas com palha no lote
    [rTotAveNoHuskBatch] [float] NULL,              -- Média % de espigas sem palha no lote
    [rTotAveHasKernelsBatch] [float] NULL,          -- Média % área granada no lote
    [rTotAveNoKernelsBatch] [float] NULL,           -- Média % área degranada no lote
    [rTotAveKernelsBatch] [float] NULL              -- Média % sementes soltas no lote
);

PRINT '✅ Tabela seed_loss criada com sucesso.';
GO

-- 4. Criação dos Índices
CREATE INDEX IX_seed_loss_DataHora ON [dbo].[seed_loss] ([DataHora] DESC);
CREATE INDEX IX_seed_loss_ScaleTicket ON [dbo].[seed_loss] ([scale_ticket]);
CREATE INDEX IX_seed_loss_Linha ON [dbo].[seed_loss] ([linha]);

PRINT '✅ Índices criados.';
GO

-- 5. Verificação da estrutura
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'seed_loss'
ORDER BY ORDINAL_POSITION;
GO

PRINT '';
PRINT '🎉 Setup completo! Tabela seed_loss pronta para uso.';
PRINT '';
GO
