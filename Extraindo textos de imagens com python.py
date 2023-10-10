import re #Esta linha importa o módulo re, que é usado para trabalhar com expressões regulares. Expressões regulares são padrões de pesquisa que você pode usar para encontrar padrões em texto.
from pytesseract import pytesseract
import os #Esta linha importa o módulo os, que é usado para lidar com operações relacionadas a sistemas de arquivos, como listar arquivos em um diretório.
from PIL import Image

caminho_tesseract = "E:\\Tesseract\\tesseract.exe"
pytesseract.tesseract_cmd = caminho_tesseract #Esta linha configura o caminho do executável do Tesseract para que o PyTesseract saiba onde encontrá-lo quando for necessário.
pasta_imagens = "E:\\teste" #o diretório onde estão as imagens
arquivos_imagens = os.listdir(pasta_imagens) # Aqui, usamos o módulo "os" para listar todos os arquivos na pasta de imagens.
padrao_rg_brasileiro = r'\d{2}\.\d{3}\.\d{3}-\d'

texto_total = []

for arquivo in arquivos_imagens: #Ele vai percorrer cada arquivo na lista arquivos_imagens um por um.
    if arquivo.endswith(('.jpg', '.png', '.bmp')): #se o arquivo terminar com .jpg, .png, .bmp
        caminho_imagem = os.path.join(pasta_imagens, arquivo) #esta linha cria o caminho completo para o arquivo de imagem combinando o caminho da pasta (pasta_imagens) e o nome do arquivo (arquivo) usando a função os.path.join()

        texto = pytesseract.image_to_string(caminho_imagem) #Usamos o Tesseract OCR para extrair texto da imagem e armazenamos o resultado na variável texto.

        texto_total.append(texto)  # Adiciona o texto da imagem à lista de texto_total
        texto_completo = '\n'.join(texto_total)
        numeros_rg = re.findall(padrao_rg_brasileiro, texto_completo) #essa linha vai procurar no texto extraido da imagem o padrão do RG

        if numeros_rg:
            for rg in numeros_rg:
                print(f"Números de RG encontrado: {rg}")

                #Coloquei a lista texto_total e depois o texto_completo(onde vai contatenar todos os textos da imagem em uma única string) pq estava puxando só um RG