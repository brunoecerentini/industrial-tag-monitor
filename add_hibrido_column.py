import pyodbc
import sys

# Configurações do banco (conforme solicitado)
DB_SERVER = "10.130.253.140"
DB_PORT = 1600
# O nome do banco tem um espaço no início conforme informado: [ FMA_Seed_Loss]
DB_NAME = " FMA_Seed_Loss" 
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
        print(f"Conectando a {DB_SERVER} banco '{DB_NAME}'...")
        conn = pyodbc.connect(conn_str, timeout=10)
        return conn
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return None

def adicionar_colunas():
    conn = conectar_sql()
    if not conn:
        print("Nao foi possivel conectar ao banco de dados.")
        return

    # Lista de novas colunas para adicionar
    # Formato: (nome_coluna, tipo_sql)
    novas_colunas = [
        ("hibrido", "NVARCHAR(100)"),
        # Adicione outras colunas aqui se necessario, ex:
        # ("nova_coluna_2", "FLOAT"),
    ]
    
    try:
        cursor = conn.cursor()
        print(f"Verificando/Adicionando colunas na tabela '{DB_TABLE}'...")
        
        for col_nome, col_tipo in novas_colunas:
            print(f"   Processando coluna [{col_nome}] ({col_tipo})...")
            
            # Verifica se a coluna ja existe
            check_sql = f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{DB_TABLE}' 
                AND COLUMN_NAME = '{col_nome}'
            """
            cursor.execute(check_sql)
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"      A coluna [{col_nome}] JA EXISTE. Pulando.")
            else:
                try:
                    # Comando para adicionar a coluna
                    alter_sql = f"ALTER TABLE {DB_TABLE} ADD [{col_nome}] {col_tipo} NULL"
                    cursor.execute(alter_sql)
                    conn.commit()
                    print(f"      Sucesso: Coluna [{col_nome}] adicionada.")
                except Exception as e:
                    print(f"      Erro ao adicionar [{col_nome}]: {e}")
        
        print("\nProcesso concluido.")
        
    except Exception as e:
        print(f"Erro geral: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    adicionar_colunas()


