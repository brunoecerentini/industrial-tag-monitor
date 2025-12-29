"""
SEED LOSS MONITOR - VERSÃO SERVIÇO
Otimizado para rodar como serviço Windows via NSSM
Com logging em arquivo e limpeza automática de cache
"""

import time
import csv
import os
import sys
import gc
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from opcua import Client

# Tenta importar pyodbc
try:
    import pyodbc
except ImportError:
    print("ERRO CRITICO: A biblioteca 'pyodbc' nao esta instalada.")
    print("Para conectar ao SQL Server, voce precisa instalar: pip install pyodbc")
    sys.exit(1)

# ================= CONFIGURAÇÕES =================
# Diretório base (onde o script está)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)  # Garante que trabalha no diretório correto

# OPC UA (KEPServer)
OPC_IP = "10.130.106.61"
OPC_PORT = 49320
OPC_URL = f"opc.tcp://{OPC_IP}:{OPC_PORT}"
NAMESPACE_INDEX = 2

# SQL Server
DB_SERVER = "10.130.254.40"
DB_PORT = 1600
DB_NAME = "ITU_Seed_Loss"
DB_TABLE = "seed_loss"

# Arquivos
ARQUIVO_CONFIG = os.path.join(BASE_DIR, "tags_config.csv")
ARQUIVO_BACKUP = os.path.join(BASE_DIR, "backup_seed_loss.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "seed_loss_monitor.log")

# Intervalos
INTERVALO_SEGUNDOS = 60
CICLOS_PARA_LIMPEZA = 60  # Limpa cache a cada 60 ciclos (~1 hora)
MAX_LOG_SIZE_MB = 10  # Tamanho máximo do arquivo de log
MAX_LOG_FILES = 5  # Número máximo de arquivos de log rotacionados
DIAS_MANTER_BACKUP = 30  # Dias para manter arquivo de backup

# Mapeamento SRT -> Linha
MAPA_LINHA = {
    "SRT1": "A",
    "SRT2": "B",
    "SRT3": "C"
}

# =================================================
# CONFIGURAÇÃO DE LOGGING
# =================================================
def configurar_logging():
    """Configura logging com rotação de arquivos."""
    # Criar diretório de logs se não existir
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Configurar logger
    logger = logging.getLogger('SeedLossMonitor')
    logger.setLevel(logging.INFO)
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
        backupCount=MAX_LOG_FILES,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Logger global
logger = configurar_logging()

# =================================================
# FUNÇÕES DE LIMPEZA
# =================================================
def limpar_cache_memoria():
    """Força coleta de lixo para liberar memória."""
    gc.collect()
    logger.info("Cache de memoria limpo (gc.collect)")

def limpar_logs_antigos():
    """Remove arquivos de log muito antigos."""
    try:
        if os.path.exists(LOG_DIR):
            agora = datetime.now()
            for arquivo in os.listdir(LOG_DIR):
                caminho = os.path.join(LOG_DIR, arquivo)
                if os.path.isfile(caminho):
                    modificado = datetime.fromtimestamp(os.path.getmtime(caminho))
                    if (agora - modificado).days > DIAS_MANTER_BACKUP:
                        os.remove(caminho)
                        logger.info(f"Log antigo removido: {arquivo}")
    except Exception as e:
        logger.warning(f"Erro ao limpar logs antigos: {e}")

def gerenciar_backup_csv():
    """Gerencia tamanho do arquivo de backup CSV."""
    try:
        if os.path.exists(ARQUIVO_BACKUP):
            tamanho_mb = os.path.getsize(ARQUIVO_BACKUP) / (1024 * 1024)
            if tamanho_mb > 50:  # Se backup > 50MB
                # Renomeia para backup com data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                novo_nome = ARQUIVO_BACKUP.replace('.csv', f'_{timestamp}.csv')
                os.rename(ARQUIVO_BACKUP, novo_nome)
                logger.info(f"Backup CSV rotacionado: {novo_nome}")
    except Exception as e:
        logger.warning(f"Erro ao gerenciar backup CSV: {e}")

# =================================================
# FUNÇÕES PRINCIPAIS
# =================================================
def carregar_tags_do_csv():
    """Carrega tags do CSV e agrupa por linha (SRT1, SRT2, etc)."""
    tags_por_linha = {}
    
    if not os.path.exists(ARQUIVO_CONFIG):
        logger.error(f"Arquivo {ARQUIVO_CONFIG} nao encontrado!")
        return {}
    
    with open(ARQUIVO_CONFIG, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        
        for row in reader:
            if not row or not row[0].strip():
                continue
                
            tag_path = row[0].strip()
            
            linha = None
            for srt_key, linha_nome in MAPA_LINHA.items():
                if srt_key in tag_path:
                    linha = linha_nome
                    break
            
            if not linha:
                logger.warning(f"Tag ignorada (SRT nao identificado): {tag_path}")
                continue
            
            coluna = tag_path.split('.')[-1]
            
            if linha not in tags_por_linha:
                tags_por_linha[linha] = {}
            
            tags_por_linha[linha][coluna] = tag_path
    
    return tags_por_linha

def conectar_sql():
    """Cria e retorna uma conexão com o SQL Server."""
    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_NAME};"
            "Trusted_Connection=yes;"
            "Network=DBMSSOCN;"
        )
        conn = pyodbc.connect(conn_str, timeout=5)
        return conn
    except Exception as e:
        logger.warning(f"Falha ao conectar no SQL Server: {e}")
        return None

def salvar_csv_backup(linha, valores_dict):
    """Salva em CSV local caso o SQL falhe."""
    arquivo_existe = os.path.exists(ARQUIVO_BACKUP)
    
    header = ['DataHora', 'linha'] + list(valores_dict.keys())
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), linha] + list(valores_dict.values())
    
    try:
        with open(ARQUIVO_BACKUP, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            if not arquivo_existe:
                writer.writerow(header)
            writer.writerow(row)
        logger.info(f"Backup local salvo para linha {linha}")
    except Exception as e:
        logger.error(f"Erro ao salvar backup: {e}")

def fix_db_schema_overflow():
    """Tenta alterar colunas para BIGINT para evitar overflow."""
    logger.info("Verificando esquema do banco de dados para evitar overflow...")
    conn = conectar_sql()
    if not conn:
        logger.warning("Nao foi possivel conectar para verificar esquema.")
        return

    columns_to_fix = [
        "dStatus",
        "dInstHuskEars", "dInstNoHuskEars", "dInstTotalEars",
        "dTotHuskSample", "dTotNoHuskSample", "dTotEarsSample", "dSampleTime",
        "dTotHuskBatch", "dTotNoHuskBatch", "dTotEarsBatch", "dBatchTime"
    ]
    
    try:
        cursor = conn.cursor()
        for col in columns_to_fix:
            try:
                # Tenta alterar para BIGINT. Se ja for, nao tem problema.
                sql = f"ALTER TABLE {DB_TABLE} ALTER COLUMN [{col}] BIGINT NULL"
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                # Ignora erro se coluna nao existir ou outro problema
                pass
        cursor.close()
        logger.info("Verificacao de esquema concluida (colunas atualizadas para BIGINT).")
    except Exception as e:
        logger.error(f"Erro ao verificar esquema: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

def inserir_no_sql(conn, linha, valores_dict):
    """Insere um registro no SQL para uma linha específica."""
    try:
        cursor = conn.cursor()
        
        colunas = ['linha'] + list(valores_dict.keys())
        valores = [linha] + list(valores_dict.values())
        
        cols_str = ", ".join([f"[{c}]" for c in colunas])
        params_str = ", ".join(["?"] * len(colunas))
        
        sql = f"INSERT INTO {DB_TABLE} ({cols_str}) VALUES ({params_str})"
        
        cursor.execute(sql, valores)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"Erro SQL linha {linha}: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("SEED LOSS MONITOR - ITU (SERVICO)")
    logger.info("Monitoramento de Perda de Sementes")
    logger.info(f"Diretorio base: {BASE_DIR}")
    logger.info("=" * 60)
    
    # Tenta corrigir esquema do banco para suportar números grandes
    fix_db_schema_overflow()
    
    # Carregar tags
    tags_por_linha = carregar_tags_do_csv()
    
    if not tags_por_linha:
        logger.error("Nenhuma tag configurada!")
        return
    
    logger.info(f"Linhas configuradas: {list(tags_por_linha.keys())}")
    for linha, tags in tags_por_linha.items():
        logger.info(f"Linha {linha}: {len(tags)} tags")
    
    # Contador para limpeza periódica
    ciclo_count = 0
    
    client = Client(OPC_URL)
    
    while True:
        try:
            logger.info(f"Conectando ao OPC UA ({OPC_URL})...")
            client.connect()
            logger.info("Conectado ao OPC UA!")
            
            while True:
                ciclo_count += 1
                timestamp = datetime.now()
                logger.info(f"Ciclo {ciclo_count}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Limpeza periódica
                if ciclo_count % CICLOS_PARA_LIMPEZA == 0:
                    logger.info("Executando limpeza periodica...")
                    limpar_cache_memoria()
                    limpar_logs_antigos()
                    gerenciar_backup_csv()
                
                conn = conectar_sql()
                
                for linha, tags in tags_por_linha.items():
                    valores_lidos = {}
                    erros = 0
                    
                    for coluna, tag_path in tags.items():
                        try:
                            node_id = f"ns={NAMESPACE_INDEX};s={tag_path}"
                            node = client.get_node(node_id)
                            val = node.get_value()
                            
                            if isinstance(val, (int, float)):
                                valores_lidos[coluna] = val
                            elif isinstance(val, bool):
                                valores_lidos[coluna] = 1 if val else 0
                            elif isinstance(val, str):
                                valores_lidos[coluna] = val
                            else:
                                try:
                                    valores_lidos[coluna] = float(val) if val is not None else None
                                except:
                                    valores_lidos[coluna] = str(val) if val is not None else None
                                    
                        except Exception as e:
                            erros += 1
                            valores_lidos[coluna] = None
                            if erros <= 3:
                                logger.warning(f"Erro tag {coluna}: {e}")
                    
                    logger.info(f"Linha {linha}: {len(valores_lidos) - erros}/{len(tags)} tags OK")
                    
                    sucesso = False
                    if conn:
                        sucesso = inserir_no_sql(conn, linha, valores_lidos)
                        if sucesso:
                            logger.info(f"SQL OK - Linha {linha}")
                    
                    if not sucesso:
                        salvar_csv_backup(linha, valores_lidos)
                
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                
                # Limpar variáveis do ciclo
                del valores_lidos
                if ciclo_count % 10 == 0:
                    gc.collect()
                
                time.sleep(INTERVALO_SEGUNDOS)
                
        except KeyboardInterrupt:
            logger.info("Parando monitor (KeyboardInterrupt)...")
            break
        except Exception as e:
            logger.error(f"Erro na conexao OPC: {e}")
            logger.info("Tentando reconectar em 30 segundos...")
            try:
                client.disconnect()
            except:
                pass
            time.sleep(30)
            continue
    
    try:
        client.disconnect()
        logger.info("Desconectado do OPC UA.")
    except:
        pass

if __name__ == "__main__":
    main()

