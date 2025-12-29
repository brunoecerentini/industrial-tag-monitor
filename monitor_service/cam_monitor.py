import time
import csv
import os
from datetime import datetime
from opcua import Client, ua

# ================= CONFIGURAÇÕES =================
IP = "10.130.106.61"
PORT = 49320
URL = f"opc.tcp://{IP}:{PORT}"
NAMESPACE_INDEX = 2  # ns=2 conforme seu exemplo

ARQUIVO_CONFIG = "tags_config.csv"
ARQUIVO_SAIDA = "monitoramento_log.csv"
INTERVALO_SEGUNDOS = 60  # 1 minuto
# =================================================

def carregar_tags_do_csv():
    """Lê o arquivo CSV e retorna uma lista de endereços de tags."""
    tags = []
    if not os.path.exists(ARQUIVO_CONFIG):
        print(f"❌ Arquivo {ARQUIVO_CONFIG} não encontrado!")
        return []
    
    with open(ARQUIVO_CONFIG, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Pula o cabeçalho se existir
        header = next(reader, None)
        
        for row in reader:
            if row and row[0].strip():  # Se a linha não estiver vazia
                tags.append(row[0].strip())
    
    print(f"📋 {len(tags)} tags carregadas do arquivo de configuração.")
    return tags

def inicializar_csv_saida(tags):
    """Cria o arquivo de saída com cabeçalho se ele não existir."""
    arquivo_existe = os.path.exists(ARQUIVO_SAIDA)
    
    if not arquivo_existe:
        with open(ARQUIVO_SAIDA, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';') # Usando ; para facilitar abrir no Excel BR
            # Cabeçalho: DataHora + nomes das tags
            header = ['Data_Hora'] + [t.split('.')[-1] for t in tags]
            writer.writerow(header)
        print(f"📁 Arquivo {ARQUIVO_SAIDA} criado com sucesso.")
    else:
        print(f"📁 Usando arquivo existente: {ARQUIVO_SAIDA}")

def main():
    print("🔄 Iniciando Monitor de Tags (Cam Monitor)...")
    
    # 1. Carregar Configurações
    tags_paths = carregar_tags_do_csv()
    if not tags_paths:
        print("⚠️ Nenhuma tag para monitorar. Encerrando.")
        return

    # 2. Preparar CSV de Saída
    inicializar_csv_saida(tags_paths)

    client = Client(URL)

    try:
        # 3. Conexão
        print(f"🔌 Conectando ao servidor {URL}...")
        client.connect()
        print("✅ Conectado com sucesso!")
        
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            valores_linha = [timestamp]
            print(f"\n⏱️  Leitura: {timestamp}")

            # 4. Ler cada tag
            for tag_path in tags_paths:
                try:
                    # Monta o Node ID: ns=2;s=Caminho.Da.Tag
                    node_id = f"ns={NAMESPACE_INDEX};s={tag_path}"
                    node = client.get_node(node_id)
                    
                    # Lê o valor
                    valor = node.get_value()
                    valores_linha.append(valor)
                    
                    # Print simples para debug no terminal
                    nome_curto = tag_path.split('.')[-1]
                    print(f"   ✔️ {nome_curto}: {valor}")

                except Exception as e:
                    print(f"   ❌ Erro na tag {tag_path}: {e}")
                    valores_linha.append("ERRO")

            # 5. Salvar no CSV
            # Abrimos e fechamos o arquivo a cada escrita para garantir que 
            # os dados sejam salvos mesmo se o computador desligar abruptamente
            with open(ARQUIVO_SAIDA, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(valores_linha)
            
            print(f"💾 Dados salvos em {ARQUIVO_SAIDA}")
            
            # 6. Aguardar próximo ciclo
            time.sleep(INTERVALO_SEGUNDOS)

    except KeyboardInterrupt:
        print("\n🛑 Monitoramento interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro fatal na conexão ou execução: {e}")
    finally:
        try:
            client.disconnect()
            print("🔌 Desconectado.")
        except:
            pass

if __name__ == "__main__":
    main()

