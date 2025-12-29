"""
Script para ESCREVER valores em tags do KEPServerEX via OPC UA.
Lê o arquivo CSV com os híbridos e permite alterar os valores no CLP.
"""

import csv
import os
import sys
from datetime import datetime
from opcua import Client, ua

# ================= CONFIGURAÇÕES =================
# OPC UA (KEPServer)
OPC_IP = "10.130.102.61"
OPC_PORT = 49320
OPC_URL = f"opc.tcp://{OPC_IP}:{OPC_PORT}"
NAMESPACE_INDEX = 2  # ns=2 padrão do KEPServer

# Nome do arquivo CSV
NOME_CSV = "Lista_Tags_hibridos.csv"
# =================================================


def encontrar_csv():
    """
    Procura o arquivo CSV em vários locais possíveis.
    """
    # Diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório atual de execução
    current_dir = os.getcwd()
    
    # Locais para procurar
    locais = [
        os.path.join(script_dir, NOME_CSV),           # Junto do script
        os.path.join(current_dir, NOME_CSV),          # Diretório atual
        NOME_CSV,                                      # Caminho relativo
    ]
    
    for local in locais:
        if os.path.exists(local):
            return local
    
    return None


def carregar_tags_do_csv(arquivo=None):
    """
    Carrega as tags do CSV.
    Coluna 'Address' = endereço da tag no KEPServer
    Coluna 'Value' = valor a ser escrito na tag
    
    Retorna lista de dicionários: [{address, type, value}, ...]
    """
    tags = []
    
    # Se não passou arquivo, tenta encontrar automaticamente
    if arquivo is None:
        arquivo = encontrar_csv()
    
    if arquivo is None or not os.path.exists(arquivo):
        print(f"❌ Arquivo CSV não encontrado!")
        print(f"\n📁 Procurei em:")
        print(f"   - Diretório do script: {os.path.dirname(os.path.abspath(__file__))}")
        print(f"   - Diretório atual: {os.getcwd()}")
        print(f"\n💡 Coloque o arquivo '{NOME_CSV}' no mesmo diretório do script,")
        print(f"   ou informe o caminho completo abaixo:")
        
        caminho_manual = input("\n📂 Caminho do CSV (ou Enter para sair): ").strip()
        
        if caminho_manual:
            # Remove aspas se o usuário copiou o caminho com aspas
            caminho_manual = caminho_manual.strip('"').strip("'")
            if os.path.exists(caminho_manual):
                arquivo = caminho_manual
            else:
                print(f"❌ Arquivo '{caminho_manual}' não encontrado!")
                return []
        else:
            return []
    
    print(f"📄 Usando arquivo: {arquivo}")
    
    # Tenta diferentes encodings e delimitadores
    # utf-8-sig primeiro para lidar com BOM automaticamente
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    delimitadores = [',', ';', '\t']
    
    conteudo = None
    encoding_usado = None
    
    # Primeiro, lê o arquivo com encoding correto
    for enc in encodings:
        try:
            with open(arquivo, 'r', encoding=enc) as f:
                conteudo = f.read()
                encoding_usado = enc
                break
        except UnicodeDecodeError:
            continue
    
    if conteudo is None:
        print("❌ Não foi possível ler o arquivo (problema de encoding)")
        return []
    
    # Remove BOM manualmente se ainda existir (caractere \ufeff)
    conteudo = conteudo.lstrip('\ufeff')
    
    # Detecta o delimitador
    primeira_linha = conteudo.split('\n')[0]
    delimitador_usado = ','
    for delim in delimitadores:
        if delim in primeira_linha:
            delimitador_usado = delim
            break
    
    print(f"   Encoding: {encoding_usado}, Delimitador: '{delimitador_usado}'")
    
    # Parse do CSV
    linhas = conteudo.strip().split('\n')
    if len(linhas) < 2:
        print("❌ Arquivo CSV vazio ou sem dados!")
        return []
    
    # Cabeçalho
    cabecalho = [col.strip().lower() for col in linhas[0].split(delimitador_usado)]
    print(f"   Colunas encontradas: {cabecalho}")
    
    # Encontra índices das colunas
    try:
        idx_address = cabecalho.index('address')
    except ValueError:
        print("❌ Coluna 'Address' não encontrada no CSV!")
        print(f"   Colunas disponíveis: {cabecalho}")
        return []
    
    idx_type = cabecalho.index('type') if 'type' in cabecalho else -1
    idx_value = cabecalho.index('value') if 'value' in cabecalho else -1
    
    # Processa as linhas de dados
    for linha in linhas[1:]:
        if not linha.strip():
            continue
        
        colunas = linha.split(delimitador_usado)
        
        if len(colunas) > idx_address:
            address = colunas[idx_address].strip()
            tipo = colunas[idx_type].strip() if idx_type >= 0 and len(colunas) > idx_type else 'String'
            value = colunas[idx_value].strip() if idx_value >= 0 and len(colunas) > idx_value else ''
            
            if address:
                tags.append({
                    'address': address,
                    'type': tipo if tipo else 'String',
                    'value': value
                })
    
    return tags


def converter_valor(valor_str, tipo):
    """
    Converte o valor string para o tipo correto do OPC UA.
    """
    tipo_lower = tipo.lower()
    
    if tipo_lower == 'string':
        return valor_str
    elif tipo_lower in ['int', 'integer', 'int16', 'int32', 'int64']:
        return int(valor_str)
    elif tipo_lower in ['float', 'real', 'double']:
        return float(valor_str)
    elif tipo_lower in ['bool', 'boolean']:
        return valor_str.lower() in ['true', '1', 'sim', 'yes']
    else:
        # Retorna como string por padrão
        return valor_str


def obter_variant_type(tipo):
    """
    Retorna o ua.VariantType correspondente ao tipo da tag.
    """
    tipo_lower = tipo.lower()
    
    if tipo_lower == 'string':
        return ua.VariantType.String
    elif tipo_lower in ['int', 'integer', 'int16']:
        return ua.VariantType.Int16
    elif tipo_lower in ['int32']:
        return ua.VariantType.Int32
    elif tipo_lower in ['int64']:
        return ua.VariantType.Int64
    elif tipo_lower in ['float', 'real']:
        return ua.VariantType.Float
    elif tipo_lower in ['double']:
        return ua.VariantType.Double
    elif tipo_lower in ['bool', 'boolean']:
        return ua.VariantType.Boolean
    else:
        return ua.VariantType.String


def escrever_tag(client, address, valor, tipo):
    """
    Escreve um valor em uma tag específica.
    
    Args:
        client: Cliente OPC UA conectado
        address: Endereço da tag (ex: FMA1.Despalha300.db_hibridos.1)
        valor: Valor a ser escrito
        tipo: Tipo do dado (String, Int, Float, etc.)
    
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        node_id = f"ns={NAMESPACE_INDEX};s={address}"
        node = client.get_node(node_id)
        
        # Converter valor para o tipo correto
        valor_convertido = converter_valor(valor, tipo)
        variant_type = obter_variant_type(tipo)
        
        # Criar o DataValue para escrita
        data_value = ua.DataValue(ua.Variant(valor_convertido, variant_type))
        
        # Escrever no nó
        node.set_data_value(data_value)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao escrever em {address}: {e}")
        return False


def ler_tag(client, address):
    """
    Lê o valor atual de uma tag.
    """
    try:
        node_id = f"ns={NAMESPACE_INDEX};s={address}"
        node = client.get_node(node_id)
        return node.get_value()
    except Exception as e:
        return f"ERRO: {e}"


def escrever_todas_tags(client, tags, confirmar=True):
    """
    Escreve os valores em todas as tags do CSV.
    """
    print(f"\n📝 Preparando para escrever {len(tags)} tags...")
    print("-" * 60)
    
    # Mostrar preview
    for i, tag in enumerate(tags, 1):
        print(f"  {i:2}. {tag['address']}")
        print(f"      Tipo: {tag['type']} | Novo Valor: {tag['value']}")
    
    print("-" * 60)
    
    if confirmar:
        resposta = input("\n⚠️  Confirma a escrita de TODOS os valores? (s/n): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada pelo usuário.")
            return
    
    print("\n🔄 Iniciando escrita...")
    sucesso = 0
    falha = 0
    
    for tag in tags:
        resultado = escrever_tag(client, tag['address'], tag['value'], tag['type'])
        
        if resultado:
            print(f"   ✅ {tag['address']} = {tag['value']}")
            sucesso += 1
        else:
            falha += 1
    
    print("-" * 60)
    print(f"📊 Resultado: {sucesso} sucesso(s), {falha} falha(s)")


def escrever_tag_individual(client, tags):
    """
    Menu para escrever em uma tag específica.
    """
    print("\n📋 Tags disponíveis:")
    print("-" * 60)
    
    for i, tag in enumerate(tags, 1):
        valor_atual = ler_tag(client, tag['address'])
        nome_curto = tag['address'].split('.')[-1]
        print(f"  {i:2}. {nome_curto:<20} = {valor_atual}")
    
    print("-" * 60)
    
    try:
        escolha = int(input("\nDigite o número da tag (0 para cancelar): "))
        
        if escolha == 0:
            return
        
        if escolha < 1 or escolha > len(tags):
            print("❌ Número inválido!")
            return
        
        tag = tags[escolha - 1]
        
        print(f"\n🏷️  Tag selecionada: {tag['address']}")
        print(f"   Tipo: {tag['type']}")
        print(f"   Valor atual (CSV): {tag['value']}")
        print(f"   Valor atual (OPC): {ler_tag(client, tag['address'])}")
        
        novo_valor = input("\n📝 Digite o novo valor: ")
        
        if not novo_valor:
            print("❌ Valor vazio! Operação cancelada.")
            return
        
        confirma = input(f"⚠️  Confirma escrever '{novo_valor}' em {tag['address']}? (s/n): ")
        
        if confirma.lower() == 's':
            if escrever_tag(client, tag['address'], novo_valor, tag['type']):
                print(f"✅ Valor escrito com sucesso!")
                print(f"   Verificação: {ler_tag(client, tag['address'])}")
            else:
                print("❌ Falha ao escrever o valor.")
        else:
            print("❌ Operação cancelada.")
            
    except ValueError:
        print("❌ Entrada inválida!")


def visualizar_valores_atuais(client, tags):
    """
    Mostra os valores atuais de todas as tags.
    """
    print("\n📊 Valores atuais das tags:")
    print("-" * 70)
    print(f"{'#':<4} {'Tag':<40} {'Valor Atual':<20}")
    print("-" * 70)
    
    for i, tag in enumerate(tags, 1):
        valor = ler_tag(client, tag['address'])
        nome_curto = tag['address'].split('.')[-1]
        print(f"{i:<4} {nome_curto:<40} {str(valor):<20}")
    
    print("-" * 70)


def menu_principal():
    """
    Menu interativo principal.
    """
    print("=" * 60)
    print("🌽 ESCRITOR DE TAGS - HÍBRIDOS")
    print(f"   Servidor: {OPC_URL}")
    print("=" * 60)
    
    # Carregar tags
    tags = carregar_tags_do_csv()
    
    if not tags:
        print("❌ Nenhuma tag encontrada. Verifique o arquivo CSV.")
        return
    
    print(f"\n📋 {len(tags)} tags carregadas do arquivo CSV")
    
    # Conectar ao OPC
    client = Client(OPC_URL)
    
    try:
        print(f"\n🔌 Conectando ao OPC UA...")
        client.connect()
        print("✅ Conectado com sucesso!")
        
        while True:
            print("\n" + "=" * 40)
            print("📌 MENU PRINCIPAL")
            print("=" * 40)
            print("  1. Visualizar valores atuais")
            print("  2. Escrever em uma tag específica")
            print("  3. Escrever TODAS as tags do CSV")
            print("  4. Recarregar arquivo CSV")
            print("  0. Sair")
            print("-" * 40)
            
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                visualizar_valores_atuais(client, tags)
                
            elif opcao == '2':
                escrever_tag_individual(client, tags)
                
            elif opcao == '3':
                escrever_todas_tags(client, tags)
                
            elif opcao == '4':
                tags = carregar_tags_do_csv()
                print(f"🔄 {len(tags)} tags recarregadas.")
                
            elif opcao == '0':
                print("\n👋 Encerrando...")
                break
            else:
                print("❌ Opção inválida!")
                
    except KeyboardInterrupt:
        print("\n\n🛑 Interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro de conexão: {e}")
    finally:
        try:
            client.disconnect()
            print("🔌 Desconectado do OPC UA.")
        except:
            pass


def escrever_direto(valores_novos):
    """
    Função para uso programático - escreve um dicionário de valores.
    
    Args:
        valores_novos: dict no formato {indice: novo_valor}
                       Ex: {1: "HIBRIDO_A", 5: "HIBRIDO_B"}
    
    Exemplo de uso:
        from escrever_tags_hibridos import escrever_direto
        escrever_direto({1: "P3282NEW", 2: "B2801NEW"})
    """
    tags = carregar_tags_do_csv()
    
    if not tags:
        print("❌ Nenhuma tag encontrada.")
        return False
    
    client = Client(OPC_URL)
    
    try:
        client.connect()
        print("✅ Conectado!")
        
        for indice, novo_valor in valores_novos.items():
            if 1 <= indice <= len(tags):
                tag = tags[indice - 1]
                if escrever_tag(client, tag['address'], novo_valor, tag['type']):
                    print(f"✅ Tag {indice}: {novo_valor}")
                else:
                    print(f"❌ Tag {indice}: Falha")
            else:
                print(f"⚠️ Índice {indice} inválido!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    finally:
        try:
            client.disconnect()
        except:
            pass


if __name__ == "__main__":
    # Se passar argumentos, escreve diretamente
    # Uso: python escrever_tags_hibridos.py <indice> <valor>
    if len(sys.argv) == 3:
        try:
            indice = int(sys.argv[1])
            valor = sys.argv[2]
            escrever_direto({indice: valor})
        except ValueError:
            print("Uso: python escrever_tags_hibridos.py <indice> <valor>")
    else:
        # Menu interativo
        menu_principal()

