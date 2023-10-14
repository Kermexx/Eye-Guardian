# Antes de tudo instale no terminal > pip install PyMuPDF
# Antes de tudo instale no terminal > pip install google-cloud-vision

import os
import re
import fitz  # PyMuPDF
from google.cloud import vision

# Define o caminho para o arquivo de credenciais do Google Cloud Vision
key_path = r'E:\Lucas\Pojetos pycharm\ImagemIA\ocr-challenge-401815-40f9758a4218.json'

# Configura a variável de ambiente para apontar para o arquivo de credenciais
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

# Função para identificar a operadora de cartão de crédito com base no número
def identify_credit_card_operator(card_number):
    # Dicionário de padrões de operadoras de cartão de crédito
    card_operators = {
        "Visa": r'^4',
        "Mastercard": r'^5[1-5]',
        "American Express": r'^3[47]',
        "Discover": r'^(6011|65)',
    }
    # Verifica qual operadora o número corresponde
    for operator, pattern in card_operators.items():
        if re.match(pattern, card_number):
            return operator
    return "Desconhecida"

# Função para extrair informações sensíveis de uma imagem
def extract_sensitive_info_from_image(image_path, results):
    # Inicializa o cliente Google Cloud Vision
    client = vision.ImageAnnotatorClient()

    # Lê o conteúdo da imagem
    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Envia a imagem para análise de texto
    response = client.text_detection(image=image)

    # Extrai texto identificado na imagem
    texts = response.text_annotations

    sensitive_info = []

    # Itera sobre os textos identificados
    for text in texts:
        text = text.description

        # Aplica expressões regulares para encontrar informações sensíveis
        matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
        matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2})', text)
        matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
        matches_email = re.findall(r'\S+@\S+', text)
        matches_telefone = re.findall(r'\+\d{2} \(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4}-\d{4}', text)
        matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)

        valid_telefones = []

        # Filtra e formata números de telefone válidos
        for telefone in matches_telefone:
            numero_limpo = re.sub(r'[^\d]', '', telefone)
            if len(numero_limpo) == 11 or len(numero_limpo) == 12:
                valid_telefones.append(telefone)

        # Verifica se um RG não está contido em um CPF e adiciona à lista de informações sensíveis
        for rg in matches_rg:
            rg_in_cpf = any(rg in cpf for cpf in matches_cpf)
            if not rg_in_cpf:
                sensitive_info.append(('RG', rg))

        # Adiciona informações sensíveis encontradas
        sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
        sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
        sensitive_info.extend([('Email', email) for email in matches_email])
        sensitive_info.extend([('Telefone', telefone) for telefone in valid_telefones])

        # Identifica a operadora de cartão de crédito e adiciona à lista de informações sensíveis
        for cartao in matches_cartao_credito:
            card_number = re.sub(r'[^\d]', '', cartao)
            operator = identify_credit_card_operator(card_number)
            if operator:
                sensitive_info.append(('Cartão de Crédito', cartao, operator))
            else:
                sensitive_info.append(('Cartão de Crédito', cartao))

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[image_path] = results.get(image_path, [])
        results[image_path].extend(sensitive_info)

    return results

# Função para extrair informações sensíveis de um arquivo PDF
def extract_sensitive_info_from_pdf(pdf_path, results):
    # Inicializa o cliente Google Cloud Vision
    client = vision.ImageAnnotatorClient()

    # Abre o documento PDF com PyMuPDF (fitz)
    pdf_document = fitz.open(pdf_path)

    sensitive_info = []

    # Itera pelas páginas do PDF
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text()

        # Aplica expressões regulares para encontrar informações sensíveis
        matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', page_text)
        matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2})', page_text)
        matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', page_text)
        matches_email = re.findall(r'\S+@\S+', page_text)
        matches_telefone = re.findall(r'\+\d{2} \(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4}-\d{4}', page_text)
        matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', page_text)

        valid_telefones = []

        # Filtra e formata números de telefone válidos
        for telefone in matches_telefone:
            numero_limpo = re.sub(r'[^\d]', '', telefone)
            if len(numero_limpo) == 11 or len(numero_limpo) == 12:
                valid_telefones.append(telefone)

        # Verifica se um RG não está contido em um CPF e adiciona à lista de informações sensíveis
        for rg in matches_rg:
            rg_in_cpf = any(rg in cpf for cpf in matches_cpf)
            if not rg_in_cpf:
                sensitive_info.append(('RG', rg))

        # Adiciona informações sensíveis encontradas
        sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
        sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
        sensitive_info.extend([('Email', email) for email in matches_email])
        sensitive_info.extend([('Telefone', telefone) for telefone in valid_telefones])

        # Identifica a operadora de cartão de crédito e adiciona à lista de informações sensíveis
        for cartao in matches_cartao_credito:
            card_number = re.sub(r'[^\d]', '', cartao)
            operator = identify_credit_card_operator(card_number)
            if operator:
                sensitive_info.append(('Cartão de Crédito', cartao, operator))
            else:
                sensitive_info.append(('Cartão de Crédito', cartao))

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[pdf_path] = results.get(pdf_path, [])
        results[pdf_path].extend(sensitive_info)

    return results

# Função para processar um diretório e seus subdiretórios, incluindo arquivos PDF
def process_directory(directory_path, results):
    # Percorre a estrutura de diretórios
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Verifica se o arquivo é uma imagem ou PDF e chama a função correspondente
            if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.bmp'):
                image_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_image(image_path, results)
            elif filename.endswith('.pdf'):
                pdf_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_pdf(pdf_path, results)

# Define o caminho do diretório a ser processado
caminho_diretorio = 'E:/teste'
results = {}

# Chama a função para processar o diretório e seus subdiretórios, incluindo arquivos PDF
process_directory(caminho_diretorio, results)

# Remove duplicatas nas informações sensíveis
for image_path, data in results.items():
    results[image_path] = list(set(data))

# Exibe as informações sensíveis encontradas
for image_path, data in results.items():
    image_path = os.path.normpath(image_path)
    print(f"Informações sensíveis encontradas em: {image_path}")
    for info in data:
        # Verifica se as informações contêm a operadora de cartão de crédito
        tipo, valor, operadora = info[:3] if len(info) > 2 else (info[0], info[1], "")
        print(f"{tipo}: {valor}")
        if tipo == 'Cartão de Crédito' and len(info) > 2:
            print(f"Operadora: {operadora}")
