
import time
import csv
import os
import sys
from datetime import datetime
from opcua import Client
# Tenta importar pyodbc
try:
    import pyodbc
except ImportError:
    print("❌ ERRO CRÍTICO: A biblioteca 'pyodbc' não está instalada.")
    print("ℹ️  Para conectar ao SQL Server, você precisa instalar: pip install pyodbc")
    sys.exit(1)
# ================= CONFIGURAÇÕES =================
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
ARQUIVO_CONFIG = "tags_config.csv"
ARQUIVO_BACKUP = "backup_seed_loss.csv"
INTERVALO_SEGUNDOS = 60
# Mapeamento SRT -> Linha
MAPA_LINHA = {
    "SRT1": "A",
    "SRT2": "B",
    "SRT3": "C"  # Caso tenha futuramente
}
# =================================================
def carregar_tags_do_csv():
    """
    Carrega tags do CSV e agrupa por linha (SRT1, SRT2, etc).
    
    Retorna: {
        "A": {"bER": "ITU_Husker...SRT1.bER", "bSTATUS": "ITU_Husker...SRT1.bSTATUS", ...},
        "B": {"bER": "ITU_Husker...SRT2.bER", "bSTATUS": "ITU_Husker...SRT2.bSTATUS", ...}
    }
    """
    tags_por_linha = {}
    
    if not os.path.exists(ARQUIVO_CONFIG):
        print(f"❌ Arquivo {ARQUIVO_CONFIG} não encontrado!")
        return {}
    
    with open(ARQUIVO_CONFIG, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Pula cabeçalho
        
        for row in reader:
            if not row or not row[0].strip():
                continue
                
            tag_path = row[0].strip()
            
            # Identificar qual SRT (linha) esta tag pertence
            linha = None
            for srt_key, linha_nome in MAPA_LINHA.items():
                if srt_key in tag_path:
                    linha = linha_nome
                    break
            
            if not linha:
                print(f"⚠️  Tag ignorada (SRT não identificado): {tag_path}")
                continue
            
            # Extrair nome da coluna (última parte do path)
            # Ex: "ITU_Husker.PLC_Secador_Debulha.Seed_loss_log.SRT1.bER" -> "bER"
            coluna = tag_path.split('.')[-1]
            
            # Inicializar dicionário da linha se não existir
            if linha not in tags_por_linha:
                tags_por_linha[linha] = {}
            
            # Mapear: coluna -> tag_path completo
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
        print(f"⚠️  Falha ao conectar no SQL Server: {e}")
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
        print(f"   💾 Backup local salvo para linha {linha}")
    except Exception as e:
        print(f"   ❌ Erro ao salvar backup: {e}")
def inserir_no_sql(conn, linha, valores_dict):
    """Insere um registro no SQL para uma linha específica."""
    try:
        cursor = conn.cursor()
        
        # Adiciona a coluna 'linha' aos dados
        colunas = ['linha'] + list(valores_dict.keys())
        valores = [linha] + list(valores_dict.values())
        
        cols_str = ", ".join([f"[{c}]" for c in colunas])
        params_str = ", ".join(["?"] * len(colunas))
        
        sql = f"INSERT INTO {DB_TABLE} ({cols_str}) VALUES ({params_str})"
        
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except Exception as e:
        print(f"   ❌ Erro SQL linha {linha}: {e}")
        return False
def main():
    print("=" * 60)
    print("🌽 SEED LOSS MONITOR - ITU")
    print("   Monitoramento de Perda de Sementes")
    print("=" * 60)
    
    # Carregar tags agrupadas por linha
    tags_por_linha = carregar_tags_do_csv()
    
    if not tags_por_linha:
        print("❌ Nenhuma tag configurada!")
        return
    
    # Mostrar resumo das tags carregadas
    print(f"\n📋 Linhas configuradas: {list(tags_por_linha.keys())}")
    for linha, tags in tags_por_linha.items():
        print(f"\n   Linha {linha}: {len(tags)} tags")
        # Mostrar tags de áreas instantâneas (novas)
        tags_inst = [t for t in tags.keys() if t.startswith('rInst')]
        print(f"   └─ Tags instantâneas: {tags_inst}")
    print("-" * 60)
    client = Client(OPC_URL)
    try:
        print(f"\n🔌 Conectando ao OPC UA ({OPC_URL})...")
        client.connect()
        print("✅ Conectado ao OPC UA!")
        
        while True:
            timestamp = datetime.now()
            print(f"\n{'='*60}")
            print(f"⏱️  Ciclo: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Conectar ao SQL uma vez por ciclo
            conn = conectar_sql()
            
            # Processar cada linha (A, B, C...)
            for linha, tags in tags_por_linha.items():
                print(f"\n📍 Processando Linha {linha}...")
                
                valores_lidos = {}
                erros = 0
                
                # Ler todas as tags desta linha
                for coluna, tag_path in tags.items():
                    try:
                        node_id = f"ns={NAMESPACE_INDEX};s={tag_path}"
                        node = client.get_node(node_id)
                        val = node.get_value()
                        
                        # Converter tipos OPC para tipos SQL
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
                        if erros <= 3:  # Limita mensagens de erro
                            print(f"   ⚠️  Erro {coluna}: {e}")
                
                print(f"   ✔️  {len(valores_lidos) - erros}/{len(tags)} tags lidas com sucesso")
                
                # Inserir no SQL
                sucesso = False
                if conn:
                    sucesso = inserir_no_sql(conn, linha, valores_lidos)
                    if sucesso:
                        print(f"   🗄️  Registro inserido no SQL (Linha {linha})")
                
                # Backup se SQL falhou
                if not sucesso:
                    salvar_csv_backup(linha, valores_lidos)
            
            # Fechar conexão SQL do ciclo
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
            print(f"\n⏳ Aguardando {INTERVALO_SEGUNDOS} segundos...")
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("\n\n🛑 Parando monitor...")
    finally:
        try:
            client.disconnect()
            print("🔌 Desconectado do OPC UA.")
        except:
            pass
if __name__ == "__main__":
    main()
