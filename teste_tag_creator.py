import requests
import json
import urllib3
import csv
import os

# Tenta importar pandas e openpyxl para ler Excel
try:
    import pandas as pd
    PANDAS_DISPONIVEL = True
except ImportError:
    PANDAS_DISPONIVEL = False

# Desabilita avisos de certificado SSL inseguro (comum em ambientes locais)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KepwareConfig:
    def __init__(self, ip, port=57412, user="Administrator", password="", use_https=True):
        """
        Inicializa a conexão com a API de Configuração do Kepware.
        
        Parâmetros:
            ip: IP do servidor KepServer
            port: Porta da API (padrão 57412)
            user: Usuário (padrão "Administrator")
            password: Senha
            use_https: True para HTTPS (padrão), False para HTTP
        """
        protocolo = "https" if use_https else "http"
        self.base_url = f"{protocolo}://{ip}:{port}/config/v1/project"
        self.ip = ip
        self.port = port
        self.auth = requests.auth.HTTPBasicAuth(user, password)
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def testar_conexao(self):
        """Testa se a API do KepServer está acessível."""
        print(f"🔍 Testando conexão com {self.base_url}...")
        try:
            # Tenta fazer um GET simples para listar canais
            response = requests.get(
                f"{self.base_url}/channels", 
                auth=self.auth, 
                headers=self.headers, 
                verify=False,
                timeout=5
            )
            if response.status_code == 200:
                canais = response.json()
                print(f"✅ Conexão OK! Canais encontrados: {len(canais)}")
                for canal in canais:
                    print(f"   📁 {canal.get('common.ALLTYPES_NAME', canal)}")
                return True
            elif response.status_code == 401:
                print("❌ Erro 401: Usuário ou senha incorretos!")
                return False
            else:
                print(f"⚠️  Resposta inesperada: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Não foi possível conectar em {self.ip}:{self.port}")
            print("   Verifique se:")
            print("   1. A API de Configuração está HABILITADA no KepServer")
            print("   2. A porta está correta (padrão: 57412)")
            print("   3. O firewall permite conexões nessa porta")
            print("   4. Tente usar use_https=False se a API estiver em HTTP")
            return False
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

    def _send_request(self, method, endpoint, payload=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, auth=self.auth, headers=self.headers, verify=False, timeout=10)
            elif method == "POST":
                response = requests.post(url, auth=self.auth, headers=self.headers, data=json.dumps(payload), verify=False, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, auth=self.auth, headers=self.headers, verify=False, timeout=10)
            
            # Se for sucesso (200 ou 201)
            if response.status_code in [200, 201]:
                return True, response.json() if response.content else {}
            else:
                return False, f"Erro {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    def criar_tag_group(self, channel, device, group_name, parent_group=None):
        """
        Cria uma pasta (Tag Group) dentro de um Device.
        
        Parâmetros:
            channel: Nome do canal
            device: Nome do dispositivo
            group_name: Nome da pasta a criar
            parent_group: Caminho da pasta pai (se for subpasta)
        """
        # Monta o endpoint
        endpoint = f"channels/{channel}/devices/{device}"
        
        if parent_group:
            pastas = parent_group.replace("\\", "/").split("/")
            for pasta in pastas:
                if pasta.strip():
                    endpoint += f"/tag_groups/{pasta.strip()}"
        
        endpoint += "/tag_groups"
        
        payload = {
            "common.ALLTYPES_NAME": group_name,
            "common.ALLTYPES_DESCRIPTION": f"Pasta criada via Python"
        }
        
        success, result = self._send_request("POST", endpoint, payload)
        return success, result

    def garantir_tag_groups(self, channel, device, tag_group_path):
        """
        Garante que todas as pastas no caminho existam, criando-as se necessário.
        
        Exemplo: "Aeration/2101" vai criar:
            1. Aeration (se não existir)
            2. 2101 dentro de Aeration (se não existir)
        """
        if not tag_group_path:
            return True
        
        pastas = tag_group_path.replace("\\", "/").split("/")
        caminho_atual = ""
        
        for pasta in pastas:
            if not pasta.strip():
                continue
                
            parent = caminho_atual if caminho_atual else None
            
            # Tenta criar a pasta (se já existir, vai dar erro mas tudo bem)
            success, result = self.criar_tag_group(channel, device, pasta.strip(), parent)
            
            if success:
                print(f"   📁 Pasta '{pasta}' criada com sucesso!")
            elif "already exists" in str(result).lower():
                print(f"   📁 Pasta '{pasta}' já existe.")
            else:
                # Pode ser outro erro, mas vamos tentar continuar
                pass
            
            # Atualiza o caminho atual
            if caminho_atual:
                caminho_atual += f"/{pasta.strip()}"
            else:
                caminho_atual = pasta.strip()
        
        return True

    def criar_tag(self, channel, device, tag_name, address, data_type, description="", tag_group=None, auto_create_groups=True):
        """
        Cria uma tag dentro de um Canal e Dispositivo existentes.
        
        Parâmetros:
            channel: Nome do canal
            device: Nome do dispositivo
            tag_name: Nome da tag
            address: Endereço no PLC (ex: D100, R001)
            data_type: Tipo de dado (ver abaixo)
            description: Descrição opcional
            tag_group: Caminho da pasta/subpasta. Pode ser:
                       - None (tag na raiz do device)
                       - "Pasta1" (tag dentro de Pasta1)
                       - "Pasta1/Pasta2" (tag dentro de Pasta2, que está dentro de Pasta1)
                       - "Pasta1/Pasta2/Pasta3" (e assim por diante...)
            auto_create_groups: Se True (padrão), cria as pastas automaticamente se não existirem
        
        Tipos comuns de data_type no Kepware:
        0: String, 1: Boolean, 2: Char, 3: Byte, 4: Short, 5: Word, 
        6: Long, 7: DWord, 8: Float, 9: Double, 10: Date
        """
        # Se tiver pastas e auto_create_groups estiver ativo, garante que existam
        if tag_group and auto_create_groups:
            print(f"🔧 Verificando/criando pastas: {tag_group}")
            self.garantir_tag_groups(channel, device, tag_group)
        
        # Monta o endpoint base
        endpoint = f"channels/{channel}/devices/{device}"
        
        # Se tiver pasta(s), adiciona ao caminho
        if tag_group:
            # Divide o caminho por "/" e monta a estrutura de tag_groups
            pastas = tag_group.replace("\\", "/").split("/")
            for pasta in pastas:
                if pasta.strip():  # Ignora strings vazias
                    endpoint += f"/tag_groups/{pasta.strip()}"
        
        endpoint += "/tags"
        
        payload = {
            "common.ALLTYPES_NAME": tag_name,
            "servermain.TAG_ADDRESS": address,
            "servermain.TAG_DATA_TYPE": data_type,
            "common.ALLTYPES_DESCRIPTION": description,
            "servermain.TAG_READ_WRITE_ACCESS": 1, # 1 = Read/Write
            "servermain.TAG_SCAN_RATE_MILLISECONDS": 100
        }

        success, result = self._send_request("POST", endpoint, payload)
        
        # Monta o caminho completo para exibição
        caminho_completo = f"{channel}.{device}"
        if tag_group:
            caminho_completo += f".{tag_group.replace('/', '.')}"
        
        if success:
            print(f"✅ Tag '{tag_name}' criada com sucesso em {caminho_completo}")
        else:
            # Verifica se erro é porque tag já existe
            if "already exists" in str(result):
                print(f"⚠️  A tag '{tag_name}' já existe em {caminho_completo}.")
            else:
                print(f"❌ Falha ao criar tag '{tag_name}': {result}")


def ler_taglist_csv(arquivo):
    """
    Lê o arquivo CSV de tags com colunas separadas.
    
    Formato esperado do CSV:
        Channel, Device, Pasta1, Pasta2, Pasta3, Endereco_CLP, Tag_name
    
    As pastas podem estar vazias (suporta 0 a 3 níveis de subpastas).
    
    Retorna: Lista de dicionários com os dados de cada tag
    """
    tags = []
    
    print(f"📖 Lendo arquivo: {arquivo}")
    
    # Tenta diferentes encodings (utf-8-sig remove o BOM automaticamente)
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(arquivo, 'r', encoding=encoding) as f:
                # Detecta o delimitador automaticamente (vírgula ou TAB)
                primeira_linha = f.readline()
                f.seek(0)  # Volta ao início do arquivo
                
                # Verifica se usa TAB ou vírgula como delimitador
                if '\t' in primeira_linha:
                    delimitador = '\t'
                    print(f"🔍 Delimitador detectado: TAB")
                else:
                    delimitador = ','
                    print(f"🔍 Delimitador detectado: vírgula")
                
                reader = csv.DictReader(f, delimiter=delimitador)
                
                # Debug: mostra as colunas detectadas
                print(f"🔍 Colunas detectadas: {reader.fieldnames}")
                
                primeira_linha = True
                for row in reader:
                    # Debug: mostra a primeira linha para diagnóstico
                    if primeira_linha:
                        print(f"🔍 Primeira linha: {dict(row)}")
                        primeira_linha = False
                    
                    # Pega os valores das colunas (flexível com nomes)
                    # Tenta diferentes nomes possíveis para cada coluna
                    channel = row.get('Channel', row.get('channel', row.get('CHANNEL', ''))).strip()
                    device = row.get('Device', row.get('device', row.get('DEVICE', ''))).strip()
                    
                    # Pastas (podem estar vazias)
                    pasta1 = row.get('Pasta1', row.get('pasta1', row.get('PASTA1', ''))).strip()
                    pasta2 = row.get('Pasta2', row.get('pasta2', row.get('PASTA2', ''))).strip()
                    pasta3 = row.get('Pasta3', row.get('pasta3', row.get('PASTA3', ''))).strip()
                    
                    # Endereço no CLP (coluna Hibrido ou Endereco_CLP)
                    endereco_clp = row.get('Hibrido', row.get('hibrido', 
                                   row.get('Endereco_CLP', row.get('endereco_clp', 
                                   row.get('Address', row.get('address', '')))))).strip()
                    
                    # Nome da tag
                    tag_name = row.get('Tag_name', row.get('tag_name', 
                               row.get('TagName', row.get('tagname', '')))).strip()
                    
                    # Ignora linhas vazias
                    if not channel or not device or not tag_name:
                        continue
                    
                    # Monta o caminho das pastas dinamicamente
                    # Só inclui pastas que não estão vazias
                    pastas = []
                    if pasta1:
                        pastas.append(pasta1)
                    if pasta2:
                        pastas.append(pasta2)
                    if pasta3:
                        pastas.append(pasta3)
                    
                    tag_group = "/".join(pastas) if pastas else None
                    
                    tags.append({
                        'channel': channel,
                        'device': device,
                        'tag_group': tag_group,
                        'tag_name': tag_name,
                        'address': endereco_clp if endereco_clp else tag_name
                    })
                
                print(f"📋 Total de tags encontradas: {len(tags)}")
                return tags
                
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")
            return []
    
    print(f"❌ Não foi possível ler o arquivo com nenhum encoding")
    return []


def criar_tags_do_arquivo(kep, arquivo, data_type=8, description="Tag criada via script"):
    """
    Lê um arquivo CSV e cria todas as tags no Kepware.
    
    Parâmetros:
        kep: Instância de KepwareConfig
        arquivo: Caminho do arquivo CSV
        data_type: Tipo de dado das tags (padrão: 8 = Float)
        description: Descrição padrão das tags
    
    Formato esperado do CSV:
        Channel, Device, Pasta1, Pasta2, Pasta3, Endereco_CLP, Tag_name
        
    As pastas podem estar vazias (suporta de 0 a 3 níveis de subpastas).
    """
    tags = ler_taglist_csv(arquivo)
    
    if not tags:
        print("❌ Nenhuma tag encontrada no arquivo!")
        return
    
    print(f"\n{'='*60}")
    print(f"🚀 Iniciando criação de {len(tags)} tags...")
    print(f"{'='*60}\n")
    
    sucesso = 0
    falha = 0
    ja_existe = 0
    
    for i, tag_info in enumerate(tags, 1):
        channel = tag_info['channel']
        device = tag_info['device']
        tag_group = tag_info['tag_group']
        tag_name = tag_info['tag_name']
        address = tag_info['address']
        
        # Monta descrição do caminho para exibição
        caminho = f"{channel}.{device}"
        if tag_group:
            caminho += f".{tag_group.replace('/', '.')}"
        caminho += f".{tag_name}"
        
        print(f"\n[{i}/{len(tags)}] {caminho}")
        print(f"   📍 Endereço CLP: {address}")
        
        try:
            kep.criar_tag(
                channel=channel,
                device=device,
                tag_name=tag_name,
                address=address,
                data_type=data_type,
                description=description,
                tag_group=tag_group,
                auto_create_groups=True
            )
            sucesso += 1
        except Exception as e:
            erro_msg = str(e).lower()
            if "already exists" in erro_msg:
                ja_existe += 1
            else:
                print(f"❌ Erro ao criar tag: {e}")
                falha += 1
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMO:")
    print(f"   ✅ Criadas: {sucesso}")
    print(f"   ⚠️  Já existiam: {ja_existe}")
    print(f"   ❌ Falha: {falha}")
    print(f"   📋 Total processado: {len(tags)}")
    print(f"{'='*60}")

# ================= EXEMPLO DE USO =================
if __name__ == "__main__":
    # Configurações do seu KepServer
    KEP_IP = "10.130.102.61"  # IP do servidor KepServer
    KEP_PORT = 57412          # Porta da API (padrão 57412)
    
    # ========== AUTENTICAÇÃO ==========
    # Usuário da API do KepServer (não é usuário Windows!)
    KEP_USER = "apiuser"
    KEP_PASS = "kepAdmin2025asd"
    
    USE_HTTPS = False  # Mude para False se quiser usar HTTP (porta 57412)
    
    # Arquivo com a lista de tags (CSV ou Excel)
    ARQUIVO_TAGS = "taglist.csv"
    
    kep = KepwareConfig(
        KEP_IP, 
        port=KEP_PORT,
        user=KEP_USER, 
        password=KEP_PASS,
        use_https=USE_HTTPS
    )
    
    # PRIMEIRO: Testar se a conexão funciona
    print("=" * 50)
    if not kep.testar_conexao():
        print("\n⚠️  Corrija o problema de conexão antes de continuar!")
        print("   Dicas:")
        print("   - Tente mudar USE_HTTPS para False")
        print("   - Verifique se a porta está correta")
        print("   - Confirme se a API está habilitada no KepServer")
        exit(1)
    print("=" * 50)
    
    print(f"\n🎯 Servidor: {KEP_IP}")
    print(f"📄 Arquivo de tags: {ARQUIVO_TAGS}")
    
    # ================= CRIAR TAGS DO ARQUIVO =================
    # Lê o arquivo CSV com colunas separadas:
    #   Channel, Device, Pasta1, Pasta2, Pasta3, Hibrido (endereço CLP), Tag_name
    #
    # As pastas são DINÂMICAS - podem estar vazias!
    # Exemplos:
    #   FMA1,Debulha,Aeration,2101,,endereco,tag    -> 2 níveis (Aeration/2101)
    #   FMA1,Debulha,Estacao,,,endereco,tag         -> 1 nível (Estacao)
    #   FMA1,Debulha,,,,endereco,tag                -> 0 níveis (raiz)
    
    criar_tags_do_arquivo(
        kep=kep,
        arquivo=ARQUIVO_TAGS,
        data_type=0,  # Default - herda do CLP automaticamente
        description="Tag criada via script Python"
    )
    
    # ================= EXEMPLOS MANUAIS (OPCIONAL) =================
    # Descomente abaixo se quiser criar tags manualmente
    
    # Exemplo 1: Tag na RAIZ do device (sem pasta)
    # kep.criar_tag(
    #     channel="ITU",
    #     device="CLP1",
    #     tag_name="TagNaRaiz",
    #     address="D100",
    #     data_type=8,
    #     description="Tag criada na raiz"
    # )
    
    # Exemplo 2: Tag dentro de UMA pasta
    # kep.criar_tag(
    #     channel="ITU",
    #     device="CLP1",
    #     tag_name="TagEmPasta",
    #     address="D101",
    #     data_type=8,
    #     tag_group="MinhaPasta"
    # )
    
    # Exemplo 3: Tag dentro de SUBPASTA (até 3 níveis)
    # kep.criar_tag(
    #     channel="ITU",
    #     device="CLP1",
    #     tag_name="NovaTagPython",
    #     address="D100",
    #     data_type=8,
    #     description="Criada via Script Python",
    #     tag_group="Nivel1/Nivel2/Nivel3"
    # )