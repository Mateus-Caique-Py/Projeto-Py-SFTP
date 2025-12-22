"""
SFTP Downloader - Script automatizado para download de arquivos via SFTP
Autor: Mateus Caique Alves Silva
Descrição: Script que se conecta a servidor SFTP, baixa arquivos baseados na data
           e os renomeia para uso local.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from paramiko import Transport, SFTPClient, RSAKey

# ===== CONFIGURAÇÕES DO SISTEMA =====
# TODO: Configure estas variáveis de acordo com seu ambiente
HOST = "sftp.seuservidor.com"           # Endereço do servidor SFTP
PORT = 22                               # Porta SFTP (geralmente 22)
USERNAME = "seu_usuario_aqui"           # Seu nome de usuário
PASSPHRASE = None                       # Senha da chave SSH (se houver)
REMOTE_DIR = "/caminho/remoto/dos/arquivos"  # Diretório remoto no servidor
LOCAL_DIR_ARQV1 = r"C:\caminho\local\ARQV1"  # Diretório local para arquivos1
LOCAL_DIR_ARQV2 = r"C:\caminho\local\ARQV2"          # Diretório local para arquivos2


def exibir_banner():
    """
    Exibe um banner ASCII estilizado no início da execução.
    
    Esta função mostra informações sobre o programa de forma visualmente
    atrativa para o usuário.
    """
    banner = """
╔══════════════════════════════════════════╗
║       ███╗   ███╗   ██╗   ███████╗       ║
║       ████╗ ████║   ██║   ██╔════╝       ║
║       ██╔████╔██║   ██║   ███████╗       ║
║       ██║╚██╔╝██║   ██║   ╚════██║       ║
║       ██║ ╚═╝ ██║██╗██║██╗███████║       ║
║       ╚═╝     ╚═╝╚═╝╚═╝╚═╝╚══════╝       ║
║                                          ║
║       SFTP Downloader Automatizado       ║
║         Autor: Mateus Caique             ║ 
╚══════════════════════════════════════════╝
    """
    print(banner)


def exibir_agradecimento(arquivos_renomeados):
    """
    Exibe mensagem de agradecimento e resumo após conclusão.
    
    Parâmetros:
        arquivos_renomeados (list): Lista de caminhos completos dos arquivos processados
    """
    banner = """
╔══════════════════════════════════════════╗
║       ███╗   ███╗   ██╗   ███████╗       ║
║       ████╗ ████║   ██║   ██╔════╝       ║
║       ██╔████╔██║   ██║   ███████╗       ║
║       ██║╚██╔╝██║   ██║   ╚════██║       ║
║       ██║ ╚═╝ ██║██╗██║██╗███████║       ║
║       ╚═╝     ╚═╝╚═╝╚═╝╚═╝╚══════╝       ║
║                                          ║
║            Download Concluído            ║
║                Obrigado                  ║ 
╚══════════════════════════════════════════╝
    """
    print(banner)
    
    print(f"\n📁 Arquivos processados:")
    for caminho_arquivo in arquivos_renomeados:
        tamanho_arquivo = os.path.getsize(caminho_arquivo)
        nome_arquivo = os.path.basename(caminho_arquivo)
        tipo_arquivo = "sla" if "teste" in nome_arquivo else "TESTE/TESTE"
        print(f"   ✅ {nome_arquivo} ({tamanho_arquivo/1024/1024:.1f} MB) [{tipo_arquivo}]")


def obter_caminho_recurso(caminho_relativo):
    """
    Obtém o caminho absoluto para um recurso, funcionando em desenvolvimento e executável.
    
    Esta função é importante para garantir que o programa encontre arquivos como
    a chave SSH tanto durante desenvolvimento quanto quando empacotado como executável.
    
    Parâmetros:
        caminho_relativo (str): Caminho relativo do arquivo de recurso
    
    Retorna:
        str: Caminho absoluto para o recurso
    """
    # Verifica se está rodando como executável empacotado
    if getattr(sys, 'frozen', False):
        # Modo executável: arquivos estão embutidos
        caminho_base = sys._MEIPASS
    else:
        # Modo desenvolvimento: usa o diretório do script
        caminho_base = os.path.dirname(__file__)
    return os.path.join(caminho_base, caminho_relativo)


# Configura o caminho para o arquivo de chave SSH
# O arquivo deve se chamar 'id_rsa' e estar na mesma pasta do script
ARQUIVO_CHAVE = obter_caminho_recurso("id_rsa")


def conectar_sftp():
    """
    Estabelece conexão com o servidor SFTP usando chave privada SSH.
    
    Retorna:
        SFTPClient: Objeto cliente SFTP para operações de arquivo
    
    Exceções:
        Exception: Se a conexão falhar
    """
    # Carrega a chave privada do arquivo
    chave = RSAKey.from_private_key_file(ARQUIVO_CHAVE, password=PASSPHRASE)
    
    # Cria transporte e conecta
    transporte = Transport((HOST, PORT))
    transporte.connect(username=USERNAME, pkey=chave)
    
    # Retorna cliente SFTP
    return SFTPClient.from_transport(transporte)


def listar_arquivos_silenciosamente(cliente_sftp, diretorio_remoto):
    """
    Lista arquivos no diretório remoto sem mostrar detalhes no terminal.
    
    Parâmetros:
        cliente_sftp (SFTPClient): Cliente SFTP conectado
        diretorio_remoto (str): Caminho do diretório remoto
    
    Retorna:
        list: Lista de tuplas (caminho, timestamp_modificacao, nome, tamanho)
    """
    print("📁 Conectando ao diretório remoto...")
    todos_arquivos = []
    
    # Itera sobre cada entrada no diretório remoto
    for entrada in cliente_sftp.listdir_attr(diretorio_remoto):
        caminho_completo = diretorio_remoto.rstrip("/") + "/" + entrada.filename
        todos_arquivos.append((
            caminho_completo,
            entrada.st_mtime,
            entrada.filename,
            entrada.st_size
        ))
    
    return todos_arquivos


def obter_data_alvo():
    """
    Determina a data alvo para busca de arquivos baseada no dia da semana.
    
    Lógica:
        - Segunda-feira: busca arquivos de sexta-feira (2 dias atrás)
        - Terça-feira: busca arquivos de segunda-feira (1 dia atrás)
        - Outros dias: busca arquivos do dia anterior
    
    Retorna:
        str: Data alvo no formato "YYYY-MM-DD"
    """
    hoje = datetime.now()
    
    if hoje.weekday() == 0:  # Segunda-feira (0 = segunda)
        data_alvo = hoje - timedelta(days=2)
        print("📅 Hoje é segunda-feira, buscando arquivos de sexta-feira")
    elif hoje.weekday() == 1:  # Terça-feira (1 = terça)
        data_alvo = hoje - timedelta(days=1)
        print("📅 Hoje é terça-feira, buscando arquivos de segunda-feira")
    else:
        # Quarta a domingo: busca dia anterior
        data_alvo = hoje - timedelta(days=1)
        print(f"📅 Buscando arquivos do dia anterior")
    
    return data_alvo.strftime("%Y-%m-%d")


def encontrar_arquivos_por_data(cliente_sftp, diretorio_remoto, data_alvo):
    """
    Encontra arquivos que correspondem à data alvo e padrões específicos.
    
    Parâmetros:
        cliente_sftp (SFTPClient): Cliente SFTP conectado
        diretorio_remoto (str): Diretório remoto para busca
        data_alvo (str): Data no formato "YYYY-MM-DD"
    
    Retorna:
        list: Lista de arquivos encontrados como tuplas
    """
    arquivos_alvo = []
    
    # Obtém todos os arquivos do diretório
    todos_arquivos = listar_arquivos_silenciosamente(cliente_sftp, diretorio_remoto)
    
    # Padrões de nomes de arquivo que estamos procurando
    padroes_arquivos = [
        "TESTE_teste_Teste_TESTE",  # Arquivos1
        "TESTE_teste_Teste_TESTE"   # Arquivos2
    ]
    
    for caminho, timestamp, nome_arquivo, tamanho in todos_arquivos:
        # Verifica se o arquivo atende a todos os critérios:
        # 1. Começa com a data alvo
        # 2. Contém um dos padrões esperados
        # 3. Termina com .csv
        # 4. Não contém "Billing" no nome
        if (nome_arquivo.startswith(data_alvo) and 
            any(padrao in nome_arquivo for padrao in padroes_arquivos) and 
            nome_arquivo.endswith(".csv") and
            "NãoPegar" not in nome_arquivo):
            
            arquivos_alvo.append((caminho, timestamp, nome_arquivo, tamanho))
            print(f"✅ Arquivo encontrado: {nome_arquivo} ({tamanho/1024/1024:.1f} MB)")
    
    return arquivos_alvo


def encontrar_arquivos_alvo(cliente_sftp, diretorio_remoto):
    """
    Encontra arquivos usando lógica de data ajustada com fallback.
    
    Parâmetros:
        cliente_sftp (SFTPClient): Cliente SFTP conectado
        diretorio_remoto (str): Diretório remoto para busca
    
    Retorna:
        list: Lista de arquivos encontrados
    """
    # Obtém data alvo baseada na lógica de dia da semana
    data_alvo = obter_data_alvo()
    print(f"🔍 Procurando arquivos da data: {data_alvo}")
    
    # Busca arquivos para a data alvo
    arquivos_alvo = encontrar_arquivos_por_data(cliente_sftp, diretorio_remoto, data_alvo)
    
    # Fallback: se não encontrou nada, tenta data anterior
    if not arquivos_alvo:
        data_anterior_obj = datetime.strptime(data_alvo, "%Y-%m-%d") - timedelta(days=1)
        data_anterior = data_anterior_obj.strftime("%Y-%m-%d")
        print(f"🔍 Nenhum arquivo encontrado. Procurando data anterior: {data_anterior}")
        arquivos_alvo = encontrar_arquivos_por_data(cliente_sftp, diretorio_remoto, data_anterior)
    
    return arquivos_alvo


class GerenciadorProgresso:
    """
    Classe para gerenciar e exibir progresso de download.
    
    Atributos:
        nome_arquivo (str):             Nome do arquivo sendo baixado
        tamanho_total (int):            Tamanho total do arquivo em bytes
        baixado (int):                  Bytes já baixados
        inicio_tempo (float):           Timestamp de início do download
        ultima_atualizacao (float):     Timestamp da última atualização do display
        ultima_porcentagem (float):     Última porcentagem exibida
        concluido (bool):               Flag indicando se o download foi concluído
        primeira_atualizacao (bool):    Flag para primeira atualização do display
    """
    
    def __init__(self, nome_arquivo, tamanho_total):
        """Inicializa o gerenciador de progresso."""
        self.nome_arquivo = nome_arquivo
        self.tamanho_total = tamanho_total
        self.baixado = 0
        self.inicio_tempo = time.time()
        self.ultima_atualizacao = 0
        self.ultima_porcentagem = 0
        self.concluido = False
        self.primeira_atualizacao = True
    
    def atualizar(self, bytes_transferidos):
        """
        Atualiza o display de progresso com base nos bytes transferidos.
        
        Parâmetros:
            bytes_transferidos (int): Total de bytes transferidos até o momento
        """
        if self.concluido:
            return
            
        # Atualiza contador de bytes baixados (não excede o total)
        self.baixado = min(bytes_transferidos, self.tamanho_total)
        
        # Calcula porcentagem atual (máximo 100%)
        porcentagem_atual = min(100, (self.baixado / self.tamanho_total) * 100)
        
        tempo_atual = time.time()
        
        # Condições para atualizar o display:
        # 1. Passou tempo suficiente desde a última atualização
        # 2. Porcentagem mudou significativamente
        # 3. É a primeira atualização
        # 4. Download está quase concluído (>99.9%)
        tempo_decorrido = tempo_atual - self.ultima_atualizacao >= 0.5
        porcentagem_mudou = abs(porcentagem_atual - self.ultima_porcentagem) >= 0.5
        e_final = porcentagem_atual >= 99.9
        
        if tempo_decorrido or porcentagem_mudou or e_final or self.primeira_atualizacao:
            self.ultima_atualizacao = tempo_atual
            self.ultima_porcentagem = porcentagem_atual
            self.primeira_atualizacao = False
            
            # Calcula velocidade de download (KB/s)
            tempo_decorrido_total = tempo_atual - self.inicio_tempo
            velocidade = self.baixado / tempo_decorrido_total / 1024 if tempo_decorrido_total > 0 else 0
            
            # Calcula tempo estimado para conclusão (ETA)
            if velocidade > 0 and porcentagem_atual < 100:
                bytes_restantes = self.tamanho_total - self.baixado
                eta = bytes_restantes / (velocidade * 1024)
                
                # Formata ETA de forma legível
                if eta > 3600:
                    eta_str = f"{eta/3600:.1f}h"
                elif eta > 60:
                    eta_str = f"{eta/60:.1f}m"
                else:
                    eta_str = f"{eta:.1f}s"
            else:
                eta_str = "---"
            
            # Cria barra de progresso visual
            tamanho_barra = 25
            preenchido = int(tamanho_barra * porcentagem_atual / 100)
            barra = "█" * preenchido + "░" * (tamanho_barra - preenchido)
            
            # Atualiza linha no terminal com informações de progresso
            sys.stdout.write(f"\r📥 {self.nome_arquivo[:25]:<25} [{barra}] {porcentagem_atual:5.1f}% | "
                           f"{self.baixado/1024/1024:6.1f}MB/{self.tamanho_total/1024/1024:6.1f}MB | "
                           f"{velocidade:5.0f} KB/s | ETA: {eta_str:>6}")
            sys.stdout.flush()
            
            # Quando concluído, garante que mostra 100%
            if porcentagem_atual >= 99.9:
                self.concluido = True
                barra_final = "█" * tamanho_barra
                sys.stdout.write(f"\r📥 {self.nome_arquivo[:25]:<25} [{barra_final}] 100.0% | "
                               f"{self.tamanho_total/1024/1024:6.1f}MB/{self.tamanho_total/1024/1024:6.1f}MB | "
                               f"{velocidade:5.0f} KB/s | ETA:   ---")
                sys.stdout.flush()
                print()  # Nova linha após conclusão


def baixar_arquivo_com_progresso(cliente_sftp, caminho_remoto, diretorio_local, nome_arquivo, tamanho_arquivo):
    """
    Baixa um arquivo do servidor SFTP para o diretório local com barra de progresso.
    
    Parâmetros:
        cliente_sftp (SFTPClient): Cliente SFTP conectado
        caminho_remoto (str): Caminho completo do arquivo no servidor
        diretorio_local (str): Diretório local para salvar o arquivo
        nome_arquivo (str): Nome do arquivo
        tamanho_arquivo (int): Tamanho do arquivo em bytes
    
    Retorna:
        str: Caminho completo do arquivo baixado localmente
    
    Exceções:
        Exception: Se ocorrer erro durante o download
    """
    # Garante que o diretório local existe
    os.makedirs(diretorio_local, exist_ok=True)
    caminho_local = os.path.join(diretorio_local, nome_arquivo)
    
    print(f"📥 Iniciando download: {nome_arquivo}")
    print(f"📂 Diretório destino: {diretorio_local}")
    
    # Cria gerenciador de progresso
    progresso = GerenciadorProgresso(nome_arquivo, tamanho_arquivo)
    
    def callback_progresso(bytes_transferidos, total):
        """Callback chamado periodicamente durante o download."""
        progresso.atualizar(bytes_transferidos)
    
    try:
        # Executa download com callback de progresso
        cliente_sftp.get(caminho_remoto, caminho_local, callback=callback_progresso)
        
        # Calcula estatísticas finais
        tempo_total = time.time() - progresso.inicio_tempo
        velocidade_media = tamanho_arquivo / tempo_total / 1024 if tempo_total > 0 else 0
        print(f"✅ Download concluído em {tempo_total:.1f}s ({velocidade_media:.0f} KB/s média)")
        
    except Exception as e:
        print(f"\n❌ Erro no download: {e}")
        raise
    
    return caminho_local


def obter_diretorio_local(nome_arquivo):
    """
    Determina o diretório local correto baseado no tipo de arquivo.
    
    Parâmetros:
        nome_arquivo (str): Nome do arquivo
    
    Retorna:
        str: Caminho do diretório local apropriado
    """
    if "Teste_teste_Teste_TESTE" in nome_arquivo:
        return LOCAL_DIR_ARQV2  # Arquivos teste2 vão para diretório teste2
    else:
        return LOCAL_DIR_ARQV1  # Outros arquivos vão para diretório de teste1


def renomear_arquivos_baixados(arquivos_baixados):
    """
    Renomeia os arquivos baixados para formato padronizado com sufixo numérico.
    
    Parâmetros:
        arquivos_baixados (list): Lista de caminhos dos arquivos baixados
    
    Retorna:
        list: Lista de caminhos dos arquivos renomeados
    """
    arquivos_renomeados = []
    contador_arquivo1 = {}
    contador_arquivo2 = {}
    
    for caminho_original in arquivos_baixados:
        nome_original = os.path.basename(caminho_original)
        
        # Extrai parte da data do nome original (YYYY-MM-DD)
        parte_data = nome_original[:10]  # "2025-10-02"
        
        # Converte para formato yyyyMmdd (sem hífens)
        novo_formato_data = parte_data.replace("-", "")  # "20251002"
        
        # Determina prefixo e dicionário de contador baseado no tipo de arquivo
        if "Teste_teste_TESTE_Teste" in nome_original:
            prefixo = "Arquivo1"
            dicionario_contador = contador_arquivo1
        else:
            prefixo = "Arquivo2"
            dicionario_contador = contador_arquivo2
        
        # Incrementa contador para esta data
        if novo_formato_data not in dicionario_contador:
            dicionario_contador[novo_formato_data] = 1
        else:
            dicionario_contador[novo_formato_data] += 1
        
        # Cria novo nome com sufixo numérico se necessário
        contador = dicionario_contador[novo_formato_data]
        if contador == 1:
            novo_nome = f"{prefixo}-{novo_formato_data}.csv"
        else:
            novo_nome = f"{prefixo}-{novo_formato_data}_{contador}.csv"
        
        # Obtém diretório correto para o arquivo renomeado
        diretorio_alvo = obter_diretorio_local(nome_original)
        novo_caminho = os.path.join(diretorio_alvo, novo_nome)
        
        # Move e renomeia o arquivo
        if os.path.dirname(caminho_original) != diretorio_alvo:
            # Se em diretório diferente, move para diretório correto
            os.makedirs(diretorio_alvo, exist_ok=True)
            os.rename(caminho_original, novo_caminho)
            print(f"🔄 Arquivo movido e renomeado: {nome_original} -> {novo_nome}")
        else:
            # Se já está no diretório correto, apenas renomeia
            os.rename(caminho_original, novo_caminho)
            print(f"🔄 Arquivo renomeado: {nome_original} -> {novo_nome}")
        
        arquivos_renomeados.append(novo_caminho)
    
    return arquivos_renomeados


def principal():
    """
    Função principal que orquestra todo o processo de download.
    
    Fluxo:
    1. Exibe banner
    2. Conecta ao SFTP
    3. Encontra arquivos alvo
    4. Faz download dos arquivos
    5. Renomeia arquivos baixados
    6. Exibe resumo final
    """
    exibir_banner()
    
    try:
        print("🚀 Iniciando SFTP Downloader...")
        print(f"🔑 Procurando chave em: {ARQUIVO_CHAVE}")
        
        # Verifica se a chave SSH existe
        if not os.path.exists(ARQUIVO_CHAVE):
            print(f"❌ Chave SSH não encontrada: {ARQUIVO_CHAVE}")
            print("📁 Por favor, coloque o arquivo 'id_rsa' na mesma pasta do executável.")
            input("Pressione Enter para sair...")
            return
        
        # Conecta ao servidor SFTP
        cliente_sftp = conectar_sftp()
        
        try:
            # Encontra arquivos alvo usando lógica de data
            arquivos_alvo = encontrar_arquivos_alvo(cliente_sftp, REMOTE_DIR)
            
            # Verifica se encontrou arquivos
            if not arquivos_alvo:
                print("❌ Nenhum arquivo correspondente encontrado.")
                return
            
            # Exibe resumo dos arquivos encontrados
            print(f"\n🎯 Encontrados {len(arquivos_alvo)} arquivo(s) para download:")
            for i, (caminho, timestamp, nome_arquivo, tamanho) in enumerate(arquivos_alvo, 1):
                tipo_arquivo = "Arquivo1" if "Arquivo_Teste" in nome_arquivo else "Teste/TESTE"
                diretorio_local = obter_diretorio_local(nome_arquivo)
                print(f"  {i}. {nome_arquivo} ({tamanho/1024/1024:.1f} MB) [{tipo_arquivo}]")
            
            # Ordena arquivos por nome para consistência
            arquivos_alvo.sort(key=lambda x: x[2])
            
            # Inicia processo de download
            print(f"\n⬇️  Iniciando download de {len(arquivos_alvo)} arquivo(s)...")
            arquivos_baixados = []
            
            for caminho, timestamp, nome_arquivo, tamanho in arquivos_alvo:
                diretorio_local = obter_diretorio_local(nome_arquivo)
                caminho_local = baixar_arquivo_com_progresso(
                    cliente_sftp, caminho, diretorio_local, nome_arquivo, tamanho
                )
                arquivos_baixados.append(caminho_local)
            
            # Renomeia arquivos baixados
            print(f"\n🔄 Renomeando arquivos...")
            arquivos_renomeados = renomear_arquivos_baixados(arquivos_baixados)
            
            # Exibe resumo final
            exibir_agradecimento(arquivos_renomeados)
                
        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
        finally:
            # Fecha conexão SFTP
            cliente_sftp.close()
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Finalização do programa
    print("\n⏹️  Programa finalizado.")
    input("Pressione Enter para sair...")


# Ponto de entrada do programa
if __name__ == "__main__":
    principal()