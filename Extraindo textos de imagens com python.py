# Antes de tudo instale no terminal > pip install PyMuPDF
# Antes de tudo instale no terminal > pip install google-cloud-vision
# Antes de tudo instale no terminal > pip install python-docx
# Antes de tudo instale no terminal > pip install python-pptx
# Antes de tudo instale no terminal > pip install openpyxl

import os
import re
import fitz #PyMuPDF
from google.cloud import vision
from docx import Document  # Para lidar com arquivos DOCX
from pptx import Presentation
import openpyxl  # Para lidar com arquivos XLSX


# Define o caminho para o arquivo de credenciais do Google Cloud Vision
key_path = r'E:\Lucas\Pojetos pycharm\ImagemIA\ocr-challenge-401815-40f9758a4218.json'

# Configura a variável de ambiente para apontar para o arquivo de credenciais
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

religioes = [
    'Cristianismo',
    'Cristão',
    'Cristã',
    'Islamismo',
    'Islâmico',
    'Islâmica',
    'Hinduísmo',
    'Hindu',
    'Hinduísta',
    'Budismo',
    'Budista',
    'Sikhismo',
    'Sikh',
    'Judaísmo',
    'Judeu',
    'Judaica',
    'Bahaí',
    'Bahaísta',
    'Jainismo',
    'Jainista',
    'Espiritismo',
    'Espírita',
    'Ateísmo',
    'Ateu',
    'Ateia'
]

cores_etnias = [
    'Branco',
    'Negro',
    'Pardo',
    'Indígena',
    'Amarelo',
    'Asiático',
    'Outro / Não Declarado',
]

def extract_info_by_pattern(pattern, text, info_type, results):
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    if matches:
        results.extend([(info_type, match) for match in matches])
    return results

def format_rg(rg):
    # Remove pontos e hífens do RG e adiciona o hífen no formato desejado
    rg_limpo = re.sub(r'[^\d]', '', rg)
    return f'{rg_limpo[:-1]}.{rg_limpo[-1]}'

# Modifica a função extract_sensitive_info_from_xlsx para incluir formatação de RG
def extract_sensitive_info_from_xlsx(xlsx_path, results):
    wb = openpyxl.load_workbook(xlsx_path)

    sensitive_info = []

    # Itera sobre todas as folhas no arquivo Excel
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]

        # Itera sobre todas as células na folha
        for row in sheet.iter_rows(min_row=1, max_col=sheet.max_column, max_row=sheet.max_row, values_only=True):
            for cell_value in row:
                if cell_value:
                    # Aplica expressões regulares para encontrar informações sensíveis
                    matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})|\d{8,9}-\d{1,2}', cell_value)
                    matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})', str(cell_value))
                    matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', str(cell_value))
                    matches_email = re.findall(r'\S+@\S+', str(cell_value))
                    matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', str(cell_value))
                    matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', str(cell_value))
                    matches_genero = re.findall(r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', cell_value)
                    valid_telefones = []


                    for telefone in matches_telefone:
                        numero_limpo = re.sub(r'[^\d]', '', telefone)
                        if len(numero_limpo) == 11 or len(numero_limpo) == 12:
                            valid_telefones.append(telefone)


                    for rg in matches_rg:
                        rg_formatado = format_rg(rg)
                        rg_in_cpf = any(rg_formatado in cpf for cpf in matches_cpf)
                        if not rg_in_cpf:
                            sensitive_info.append(('RG', rg_formatado))

                    # Add sensitive information found
                    sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
                    sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
                    sensitive_info.extend([('Email', email) for email in matches_email])
                    sensitive_info.extend([('Telefone', telefone) for telefone in valid_telefones])
                    sensitive_info.extend([('Cartão de Crédito', cartao) for cartao in matches_cartao_credito])
                    sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
                    # Extrai informações sobre religiões
                    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', cell_value, 'Religião',sensitive_info)
                    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', cell_value,'Cor/Etnia', sensitive_info)
    # Add the extracted sensitive information to the results dictionary
    if sensitive_info:
        results[xlsx_path] = results.get(xlsx_path, [])
        results[xlsx_path].extend(sensitive_info)

    return results

def process_directory_with_xlsx(directory_path, results):
    # Percorre a estrutura de diretórios
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Adiciona suporte para arquivos XLSX
            if filename.endswith('.xlsx'):
                xlsx_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_xlsx(xlsx_path, results)

def extract_sensitive_info_from_pptx(pptx_path_or_text, results):
    if os.path.isfile(pptx_path_or_text):  # Verifica se é um caminho de arquivo
        presentation = Presentation(pptx_path_or_text)
        text = "\n".join([shape.text for slide in presentation.slides for shape in slide.shapes if hasattr(shape, "text")])

    else:
        text = pptx_path_or_text

    sensitive_info = []

    # Aplica expressões regulares para encontrar informações sensíveis
    matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
    matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})', text)
    matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
    matches_email = re.findall(r'\S+@\S+', text)
    matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
    matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)
    matches_genero = re.findall(r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', text)
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
    sensitive_info.extend([('Cartão de Crédito', cartao) for cartao in matches_cartao_credito])
    sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
    # Extrai informações sobre religiões
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião', sensitive_info)
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',sensitive_info)

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[pptx_path_or_text] = results.get(pptx_path_or_text, [])
        results[pptx_path_or_text].extend(sensitive_info)

    return results

# Modifica a função process_directory para incluir arquivos PPTX
def process_directory_with_pptx(directory_path, results):
    # Percorre a estrutura de diretórios
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Adiciona suporte para arquivos PPTX
            if filename.endswith('.pptx'):
                pptx_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_pptx(pptx_path, results)

# Função para extrair informações sensíveis de um arquivo PDF
def extract_sensitive_info_from_pdf(pdf_path, results):
    # Inicializa o documento PDF
    doc = fitz.open(pdf_path)

    sensitive_info = []

    # Itera sobre as páginas do documento PDF
    for page_number in range(doc.page_count):
        page = doc[page_number]

        # Extrai texto da página
        text = page.get_text()

        # Aplica expressões regulares para encontrar informações sensíveis
        matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
        matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})', text)
        matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
        matches_email = re.findall(r'\S+@\S+', text)
        matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
        matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)
        matches_genero = re.findall(r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', text)

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
        sensitive_info.extend([('Cartão de Crédito', cartao) for cartao in matches_cartao_credito])
        sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
        # Extrai informações sobre religiões
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião',sensitive_info)
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',sensitive_info)

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[pdf_path] = results.get(pdf_path, [])
        results[pdf_path].extend(sensitive_info)

    return results

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
        matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
        matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)
        matches_genero = re.findall(r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', text)
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
        sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
        # Extrai informações sobre religiões
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião',sensitive_info)
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',sensitive_info)

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


# Função para extrair informações sensíveis de um arquivo TXT

def extract_sensitive_info_from_txt(txt_path, results):
    with open(txt_path, 'r') as txt_file:
        text = txt_file.read()

    sensitive_info = []

    # Aplica expressões regulares para encontrar informações sensíveis
    matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-\d{1,2}|\d{8}-\d{1,2}|\d{7,9}-\d{1,2}', text)
    matches_cpf = re.findall(r'\b(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})\b', text)
    matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
    matches_email = re.findall(r'\S+@\S+', text)
    matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
    matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)
    matches_genero = re.findall(r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', text)

    # Verifica se um RG não está contido em um CPF e adiciona à lista de informações sensíveis
    for rg in matches_rg:
        rg_in_cpf = any(rg in cpf for cpf in matches_cpf)
        if not rg_in_cpf:
            sensitive_info.append(('RG', rg))

    # Adiciona informações sensíveis encontradas
    sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
    sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
    sensitive_info.extend([('Email', email) for email in matches_email])
    sensitive_info.extend([('Telefone', telefone) for telefone in matches_telefone])
    sensitive_info.extend([('Cartão de Crédito', cartao) for cartao in matches_cartao_credito])
    sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
    # Extrai informações sobre religiões
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião', sensitive_info)
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',sensitive_info)

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[txt_path] = results.get(txt_path, [])
        results[txt_path].extend(sensitive_info)

    return results

# Função para processar um diretório e seus subdiretórios, incluindo arquivos TXT
def process_directory_with_txt(directory_path, results):
    # Percorre a estrutura de diretórios
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Adiciona suporte para arquivos TXT
            if filename.endswith('.txt'):
                txt_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_txt(txt_path, results)


# Adiciona suporte para arquivos DOCX

import os
import re
from docx import Document

# Função para extrair informações sensíveis de um arquivo DOCX
def extract_sensitive_info_from_docx(docx_path_or_text, results):
    if os.path.isfile(docx_path_or_text):  # Verifica se é um caminho de arquivo
        with open(docx_path_or_text, 'rb') as docx_file:
            doc = Document(docx_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        text = docx_path_or_text

    sensitive_info = []

    # Aplica expressões regulares para encontrar informações sensíveis
    matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
    matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})', text)
    matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
    matches_email = re.findall(r'\S+@\S+', text)
    matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
    matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)
    matches_genero = re.findall(r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', text)

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
    sensitive_info.extend([('Cartão de Crédito', cartao) for cartao in matches_cartao_credito])
    sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
    # Extrai informações sobre religiões
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião', sensitive_info)
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',sensitive_info)

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[docx_path_or_text] = results.get(docx_path_or_text, [])
        results[docx_path_or_text].extend(sensitive_info)

    return results

# Função para processar um diretório e seus subdiretórios, incluindo arquivos DOCX
def process_directory_with_docx(directory_path, results):
    # Percorre a estrutura de diretórios
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Adiciona suporte para arquivos DOCX
            if filename.endswith('.docx'):
                docx_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_docx(docx_path, results)


# Modifica a função process_directory para incluir arquivos TXT e DOCX
def process_directory(directory_path, results):
    # Percorre a estrutura de diretórios
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            # Verifica se o arquivo é uma imagem, PDF, TXT ou DOCX e chama a função correspondente
            if filename.endswith(('.jpg', '.png', '.bmp')):
                image_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_image(image_path, results)
            elif filename.endswith('.pdf'):
                pdf_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_pdf(pdf_path, results)
            elif filename.endswith('.txt'):
                txt_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_txt(txt_path, results)
            elif filename.endswith('.docx'):
                docx_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_docx(docx_path, results)
            elif filename.endswith('.pptx'):
                pptx_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_pptx(pptx_path, results)
            elif filename.endswith('.xlsx'):
                xlsx_path = os.path.join(root, filename)
                results = extract_sensitive_info_from_xlsx(xlsx_path, results)


# Define o caminho do diretório a ser processado
caminho_diretorio = 'E:/teste'
results = {}

# Chama a função para processar o diretório e seus subdiretórios, incluindo arquivos PDF, TXT e DOCX
process_directory(caminho_diretorio, results)

# Remove duplicatas nas informações sensíveis
for path, data in results.items():
    results[path] = list(set(data))

# Exibe as informações sensíveis encontradas
for path, data in results.items():
    path = os.path.normpath(path)
    print(f"Informações sensíveis encontradas em: {path}")
    for info in data:
        tipo, valor, operadora = info[:3] if len(info) > 2 else (info[0], info[1], "")
        print(f"{tipo}: {valor}")
        if tipo == 'Cartão de Crédito' and len(info) > 2:
            print(f"Operadora: {operadora}")

