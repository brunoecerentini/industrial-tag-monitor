import pyodbc
import sys

# Configurações do banco (baseadas no cam_monitor_service.py)
DB_SERVER = "10.130.254.40"
DB_PORT = 1600
DB_NAME = "ITU_Seed_Loss"
DB_TABLE = "seed_loss"

def conectar_sql():
    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_NAME};"
            "Trusted_Connection=yes;"
            "Network=DBMSSOCN;"
        )
        print(f"Conectando a {DB_SERVER} banco {DB_NAME}...")
        conn = pyodbc.connect(conn_str, timeout=10)
        return conn
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return None

def fix_columns():
    conn = conectar_sql()
    if not conn:
        print("Nao foi possivel conectar ao banco de dados.")
        return

    # Lista de colunas INT que podem estourar (baseada no setup_seed_loss.sql)
    columns_to_fix = [
        "dStatus",
        "dInstHuskEars",
        "dInstNoHuskEars",
        "dInstTotalEars",
        "dTotHuskSample",
        "dTotNoHuskSample",
        "dTotEarsSample",
        "dSampleTime",
        "dTotHuskBatch",
        "dTotNoHuskBatch",
        "dTotEarsBatch",
        "dBatchTime"
    ]
    
    try:
        cursor = conn.cursor()
        print(f"Iniciando alteracao de colunas na tabela '{DB_TABLE}' para BIGINT...")
        
        for col in columns_to_fix:
            print(f"   Alterando coluna [{col}]...")
            try:
                # Comando para alterar o tipo da coluna
                sql = f"ALTER TABLE {DB_TABLE} ALTER COLUMN [{col}] BIGINT NULL"
                cursor.execute(sql)
                conn.commit()
                print(f"      Sucesso: [{col}] agora e BIGINT.")
            except Exception as e:
                # Pode falhar se a coluna não existir ou tiver dependências (índices, constraints)
                print(f"      Erro ao alterar [{col}]: {e}")
        
        print("\nProcesso de correcao concluido.")
        
    except Exception as e:
        print(f"Erro durante a execucao: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    fix_columns()
