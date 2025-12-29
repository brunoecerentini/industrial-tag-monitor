"""
SEED LOSS MONITOR - VERSAO CONFIGURAVEL
Para implantacao em multiplas plantas industriais
Configuracoes em config.ini
"""

import time
import csv
import os
import sys
import gc
import logging
import configparser
from datetime import datetime
from logging.handlers import RotatingFileHandler
from opcua import Client

# Tenta importar pyodbc
try:
    import pyodbc
except ImportError:
    print("ERRO CRITICO: A biblioteca 'pyodbc' nao esta instalada.")
    print("Execute: pip install pyodbc")
    sys.exit(1)

# ================= CARREGAR CONFIGURACOES =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

def carregar_configuracoes():
    """Carrega configuracoes do arquivo config.ini"""
    if not os.path.exists(CONFIG_FILE):
        print(f"ERRO: Arquivo {CONFIG_FILE} nao encontrado!")
        print("Copie o arquivo config.ini.exemplo para config.ini e configure.")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding='utf-8')
    return config

# Carregar configuracoes
CONFIG = carregar_configuracoes()

# OPC UA
OPC_IP = CONFIG.get('OPC_UA', 'ip', fallback='10.130.106.61')
OPC_PORT = CONFIG.getint('OPC_UA', 'porta', fallback=49320)
OPC_URL = f"opc.tcp://{OPC_IP}:{OPC_PORT}"
NAMESPACE_INDEX = CONFIG.getint('OPC_UA', 'namespace', fallback=2)

# SQL Server
DB_SERVER = CONFIG.get('SQL_SERVER', 'ip', fallback='10.130.254.40')
DB_PORT = CONFIG.getint('SQL_SERVER', 'porta', fallback=1600)
# Remove aspas mas MANTEM espacos (para bancos como " FMA_Seed_Loss")
DB_NAME = CONFIG.get('SQL_SERVER', 'database', fallback='ITU_Seed_Loss').strip('"').strip("'")
DB_TABLE = CONFIG.get('SQL_SERVER', 'tabela', fallback='seed_loss').strip('"').strip("'")

# Monitor
INTERVALO_SEGUNDOS = CONFIG.getint('MONITOR', 'intervalo_segundos', fallback=60)
CICLOS_PARA_LIMPEZA = CONFIG.getint('MONITOR', 'ciclos_limpeza', fallback=60)

# Planta
NOME_PLANTA = CONFIG.get('PLANTA', 'nome_planta', fallback='PLANTA')

# Arquivos
ARQUIVO_CONFIG = os.path.join(BASE_DIR, "tags_config.csv")
ARQUIVO_BACKUP = os.path.join(BASE_DIR, "backup_seed_loss.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "seed_loss_monitor.log")

# Configuracoes de log
MAX_LOG_SIZE_MB = 10
MAX_LOG_FILES = 5
DIAS_MANTER_BACKUP = 30

# Mapeamento SRT -> Linha
MAPA_LINHA = {
    "SRT1": "A",
    "SRT2": "B",
    "SRT3": "C",
    "SRO1.SRT.A": "A",
    "SRO1.SRT.B": "B"
}

# =================================================
# CONFIGURACAO DE LOGGING
# =================================================
def configurar_logging():
    """Configura logging com rotacao de arquivos."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logger = logging.getLogger('SeedLossMonitor')
    logger.setLevel(logging.INFO)
    
    # Limpar handlers existentes
    logger.handlers = []
    
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
        backupCount=MAX_LOG_FILES,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        f'%(asctime)s | {NOME_PLANTA} | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = configurar_logging()

# =================================================
# FUNCOES DE LIMPEZA
# =================================================
def limpar_cache_memoria():
    """Forca coleta de lixo para liberar memoria."""
    gc.collect()
    logger.info("Cache de memoria limpo")

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
            if tamanho_mb > 50:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                novo_nome = ARQUIVO_BACKUP.replace('.csv', f'_{timestamp}.csv')
                os.rename(ARQUIVO_BACKUP, novo_nome)
                logger.info(f"Backup CSV rotacionado: {novo_nome}")
    except Exception as e:
        logger.warning(f"Erro ao gerenciar backup CSV: {e}")

# =================================================
# FUNCOES PRINCIPAIS
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
            
            # 1. Identificar Linha (A ou B)
            linha = None
            
            # Tenta via Mapa exato
            for srt_key, linha_nome in MAPA_LINHA.items():
                if srt_key in tag_path:
                    linha = linha_nome
                    break
            
            # Se nao encontrou, busca substrings
            if not linha:
                 if ".SRT1." in tag_path or ".A." in tag_path or "SRT.A" in tag_path:
                     linha = "A"
                 elif ".SRT2." in tag_path or ".B." in tag_path or "SRT.B" in tag_path:
                     linha = "B"
                 elif ".SRT3." in tag_path or ".C." in tag_path or "SRT.C" in tag_path:
                     linha = "C"

            if not linha:
                logger.warning(f"Tag ignorada (Linha nao identificada): {tag_path}")
                continue
            
            # 2. Identificar Coluna (Nome da variavel)
            # Se a coluna for apenas o sufixo (ex: .bER), duplicatas de sufixo sobrescrevem
            # Solucao: Usar sufixo, mas avisar se duplicado
            coluna = tag_path.split('.')[-1]
            
            if linha not in tags_por_linha:
                tags_por_linha[linha] = {}
            
            # Verificar duplicidade
            if coluna in tags_por_linha[linha]:
                logger.warning(f"DUPLICIDADE DETECTADA na Linha {linha}:")
                logger.warning(f"  Existente: {tags_por_linha[linha][coluna]}")
                logger.warning(f"  Ignorando: {tag_path}")
            else:
                tags_por_linha[linha][coluna] = tag_path
    
    return tags_por_linha

def conectar_sql():
    """Cria e retorna uma conexao com o SQL Server."""
    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_NAME};"
            "Trusted_Connection=yes;"
            "Network=DBMSSOCN;"
        )
        conn = pyodbc.connect(conn_str, timeout=10)
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

def inserir_no_sql(conn, linha, valores_dict):
    """Insere um registro no SQL para uma linha especifica."""
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
    logger.info(f"SEED LOSS MONITOR - {NOME_PLANTA}")
    logger.info("=" * 60)
    logger.info(f"OPC UA: {OPC_URL}")
    logger.info(f"SQL Server: {DB_SERVER}:{DB_PORT}/{DB_NAME}")
    logger.info(f"Intervalo: {INTERVALO_SEGUNDOS}s")
    logger.info(f"Diretorio: {BASE_DIR}")
    logger.info("=" * 60)
    
    # Carregar tags
    tags_por_linha = carregar_tags_do_csv()
    
    if not tags_por_linha:
        logger.error("Nenhuma tag configurada!")
        return
    
    logger.info(f"Linhas configuradas: {list(tags_por_linha.keys())}")
    for linha, tags in tags_por_linha.items():
        logger.info(f"Linha {linha}: {len(tags)} tags")
    
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
                
                # Limpeza periodica
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

