#Antes de tudo instale no terminal > pip install google-cloud-vision

import os
import re
from google.cloud import vision

key_path = r'E:\Lucas\Pojetos pycharm\ImagemIA\ocr-challenge-401815-40f9758a4218.json'  # Caminho para o arquivo JSON com a chave de API

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

def extract_rg_numbers_from_image(image_path, results):
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)

    texts = response.text_annotations

    rgs_encontrados = []  # Usando uma lista para armazenar os RGs encontrados
    cpfs_encontrados = []  # Usando uma lista para armazenar os CPFs encontrados

    for text in texts:
        text = text.description

        # Use expressões regulares para encontrar números de RG e CPF
        matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
        matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2})', text)
        rgs_encontrados.extend(matches_rg)  # Adicione os RGs encontrados à lista
        cpfs_encontrados.extend(matches_cpf)  # Adicione os CPFs encontrados à lista

    if rgs_encontrados:
        results[image_path] = results.get(image_path, [])
        results[image_path].extend([('RG', rg) for rg in rgs_encontrados])

    if cpfs_encontrados:
        results[image_path] = results.get(image_path, [])
        results[image_path].extend([('CPF', cpf) for cpf in cpfs_encontrados])

    return results

directory_path = 'E:/teste'  # Substitua pelo caminho para o seu diretório

results = {}  # Dicionário para armazenar os resultados (imagem -> [(tipo, valor)])

for filename in os.listdir(directory_path):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        image_path = os.path.join(directory_path, filename)
        results = extract_rg_numbers_from_image(image_path, results)

# Remova duplicatas
for image_path, data in results.items():
    results[image_path] = list(set(data))

# Exiba os resultados com o caminho formatado
for image_path, data in results.items():
    image_path = os.path.normpath(image_path)  # Formata o caminho
    print(f"Dados sensíveis encontrados em: {image_path}")
    for tipo, valor in data:
        print(f"{tipo}: {valor}")
