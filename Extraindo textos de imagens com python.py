# Antes de tudo instale no terminal > pip install google-cloud-vision
# Importa as bibliotecas necessárias
import os            # Módulo para interagir com o sistema operacional
import re            # Módulo para trabalhar com expressões regulares (regex)
from google.cloud import vision  # Importa a biblioteca Google Cloud Vision

# Define o caminho para o arquivo de credenciais do Google Cloud Vision
key_path = r'E:\Lucas\Pojetos pycharm\ImagemIA\ocr-challenge-401815-40f9758a4218.json'

# Configura a variável de ambiente para apontar para o arquivo de credenciais
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

# Função para identificar a operadora de cartão de crédito com base no número
def identify_credit_card_operator(card_number):
    # Dicionário com padrões de início de números para cada operadora
    card_operators = {
        "Visa": r'^4',
        "Mastercard": r'^5[1-5]',
        "American Express": r'^3[47]',
        "Discover": r'^(6011|65)',
    }

    # Verifica se o número se encaixa em um dos padrões de operadora
    for operator, pattern in card_operators.items():
        if re.match(pattern, card_number):
            return operator
    return "Desconhecida"  # Retorna "Desconhecida" se não corresponder a nenhuma operadora

# Função para extrair informações sensíveis de uma imagem
def extract_sensitive_info_from_image(image_path, results):
    # Cria um cliente para o Google Cloud Vision
    client = vision.ImageAnnotatorClient()

    # Abre o arquivo de imagem em formato binário (rb)
    with open(image_path, 'rb') as image_file:
        content = image_file.read()  # Lê o conteúdo do arquivo

    image = vision.Image(content=content)  # Cria um objeto de imagem para análise

    response = client.text_detection(image=image)  # Realiza a detecção de texto na imagem

    texts = response.text_annotations  # Extrai as anotações de texto detectadas na imagem

    sensitive_info = []  # Inicializa uma lista para armazenar informações sensíveis encontradas

    for text in texts:
        text = text.description  # Extrai o texto do resultado da detecção

        # Define expressões regulares para detectar RG, CPF, CNPJ, e-mail, telefone e números de cartão de crédito
        matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
        matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2})', text)
        matches_cnpj = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
        matches_email = re.findall(r'\S+@\S+', text)
        matches_telefone = re.findall(r'\+\d{2} \(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4}-\d{4}', text)

        # Adicione uma expressão regular para detectar números de cartão de crédito
        matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)

        valid_telefones = []

        # Limpa os números de telefone e verifica se são válidos
        for telefone in matches_telefone:
            numero_limpo = re.sub(r'[^\d]', '', telefone)
            if len(numero_limpo) == 11 or len(numero_limpo) == 12:
                valid_telefones.append(telefone)

        for rg in matches_rg:
            rg_in_cpf = any(rg in cpf for cpf in matches_cpf)

            # Verifica se o RG não está presente nos CPFs
            if not rg_in_cpf:
                sensitive_info.append(('RG', rg))

        # Adiciona as informações sensíveis encontradas à lista
        sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
        sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
        sensitive_info.extend([('Email', email) for email in matches_email])
        sensitive_info.extend([('Telefone', telefone) for telefone in valid_telefones])

        # Processa os números de cartão de crédito
        for cartao in matches_cartao_credito:
            card_number = re.sub(r'[^\d]', '', cartao)
            operator = identify_credit_card_operator(card_number)

            # Adiciona informações de cartão de crédito com ou sem operadora
            if operator:
                sensitive_info.append(('Cartão de Crédito', cartao, operator))
            else:
                sensitive_info.append(('Cartão de Crédito', cartao))

    if sensitive_info:
        results[image_path] = results.get(image_path, [])  # Armazena informações sensíveis no dicionário de resultados
        results[image_path].extend(sensitive_info)

    return results  # Retorna o dicionário de resultados

# Função para processar um diretório e seus subdiretórios
def process_directory(directory_path, results):
    # Percorre a estrutura de diretórios usando os.walk
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Verifica se o arquivo tem uma extensão de imagem (jpg, png, bmp)
            if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.bmp'):
                image_path = os.path.join(root, filename)  # Monta o caminho completo do arquivo de imagem
                results = extract_sensitive_info_from_image(image_path, results)  # Extrai informações sensíveis da imagem

# Define o caminho do diretório a ser processado
caminho_diretorio = 'E:/teste'
results = {}  # Inicializa um dicionário para armazenar os resultados

# Chama a função para processar o diretório e seus subdiretórios
process_directory(caminho_diretorio, results)

for image_path, data in results.items():
    results[image_path] = list(set(data))  # Remove duplicatas de informações sensíveis

for image_path, data in results.items():
    image_path = os.path.normpath(image_path)  # Normaliza o caminho do arquivo
    print(f"Informações sensíveis encontradas em: {image_path}")
    for info in data:
        # Extrai tipo, valor e operadora se disponível (para cartões de crédito)
        tipo, valor, operadora = info[:3] if len(info) > 2 else (info[0], info[1], "")
        print(f"{tipo}: {valor}")
        if tipo == 'Cartão de Crédito' and len(info) > 2:
            print(f"Operadora: {operadora}")  # Imprime informações específicas para cartões de crédito
