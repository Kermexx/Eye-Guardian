#Antes de tudo instale no terminal > pip install google-cloud-vision

import os
import re
from google.cloud import vision

key_path = r'E:\Lucas\Pojetos pycharm\ImagemIA\ocr-challenge-401815-40f9758a4218.json'

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

def identify_credit_card_operator(card_number):
    # Dicionário com padrões de início de números para cada operadora
    card_operators = {
        "Visa": r'^4',
        "Mastercard": r'^5[1-5]',
        "American Express": r'^3[47]',
        "Discover": r'^(6011|65)',
        # Adicione mais operadoras e padrões, se necessário
    }

    for operator, pattern in card_operators.items():
        if re.match(pattern, card_number):
            return operator
    return "Desconhecida"

def extract_sensitive_info_from_image(image_path, results):
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)

    texts = response.text_annotations

    sensitive_info = []

    for text in texts:
        text = text.description

        matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
        matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2})', text)
        matches_cnpj = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
        matches_email = re.findall(r'\S+@\S+', text)
        matches_telefone = re.findall(r'\+\d{2} \(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4,5}-\d{4}|\(\d{2}\) \d{4}-\d{4}',
                                      text)

        # Adicione uma expressão regular para detectar números de cartão de crédito
        matches_cartao_credito = re.findall(r'(\d{4}-\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4} \d{4})', text)

        valid_telefones = []
        for telefone in matches_telefone:
            numero_limpo = re.sub(r'[^\d]', '', telefone)
            if len(numero_limpo) == 11 or len(numero_limpo) == 12:
                valid_telefones.append(telefone)

        for rg in matches_rg:
            rg_in_cpf = any(rg in cpf for cpf in matches_cpf)
            if not rg_in_cpf:
                sensitive_info.append(('RG', rg))

        sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
        sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
        sensitive_info.extend([('Email', email) for email in matches_email])
        sensitive_info.extend([('Telefone', telefone) for telefone in valid_telefones])

        for cartao in matches_cartao_credito:
            card_number = re.sub(r'[^\d]', '', cartao)
            operator = identify_credit_card_operator(card_number)
            if operator:
                sensitive_info.append(('Cartão de Crédito', cartao, operator))
            else:
                sensitive_info.append(('Cartão de Crédito', cartao))

    if sensitive_info:
        results[image_path] = results.get(image_path, [])
        results[image_path].extend(sensitive_info)

    return results

directory_path = 'E:/teste'

results = {}

for filename in os.listdir(directory_path):
    if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.bmp'):
        image_path = os.path.join(directory_path, filename)
        results = extract_sensitive_info_from_image(image_path, results)

for image_path, data in results.items():
    results[image_path] = list(set(data))

for image_path, data in results.items():
    image_path = os.path.normpath(image_path)
    print(f"Informações sensíveis encontradas em: {image_path}")
    for info in data:
        tipo, valor, operadora = info[:3] if len(info) > 2 else (info[0], info[1], "")
        print(f"{tipo}: {valor}")
        if tipo == 'Cartão de Crédito' and len(info) > 2:
            print(f"Operadora: {operadora}")
