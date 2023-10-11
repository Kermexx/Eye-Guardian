"""Bibliotecas usadas: os, pytesseract, re, PIL, cv2 (os manipula arquivos e diretórios, pytesseract extrai textos de imagens,
re encontra padrões no texto, PIL trabalha com imagens"""
import os
import pytesseract
import re
from PIL import Image
import cv2

# Configura o caminho para o executável Tesseract OCR (altere o caminho conforme necessário)
pytesseract.pytesseract.tesseract_cmd = r'E:\\Tesseract\\tesseract.exe'

RG_lista = []



def realcar_contraste(imagem):
    # Aplicar realce de contraste para realçar o texto
    contraste = ImageEnhance.Contrast(imagem)
    imagem_realcada = contraste.enhance(2.0)  # Ajuste o valor de contraste conforme necessário

    return imagem_realcada

def binarizar_imagem(caminho_imagem):
    try:
        imagem = Image.open(caminho_imagem)
        imagem_cinza = imagem.convert('L')  # Converte para escala de cinza
        _, imagem_bin = cv2.threshold(np.array(imagem_cinza), 128, 255, cv2.THRESH_BINARY)  # Binarização

        # Salvar a imagem binarizada temporariamente
        caminho_temporario = "temp_image.png"
        cv2.imwrite(caminho_temporario, imagem_bin)

        texto_extraido = extrair_texto_de_imagem(caminho_temporario)

        os.remove(caminho_temporario)  # Remove a imagem temporária

        return texto_extraido
    except Exception as e:
        print(f"Erro ao extrair texto da imagem {caminho_imagem}: {str(e)}")
        return None

def extrair_texto_de_imagem(caminho_imagem): #Esta linha define uma função chamada extrair_texto_de_imagem que precisa de um endereço (caminho) de uma imagem como entrada(não mexe nisso, o caminho_imagem vai ser definido depois).
    try:
        imagem = Image.open(caminho_imagem) #Nesta linha, abrimos a imagem usando um programa chamado PIL (Pillow) e a guardamos em uma variável chamada "imagem".
        texto = pytesseract.image_to_string(imagem, lang='eng') #Aqui, usamos um programa chamado Tesseract para pegar o texto da imagem que abrimos na etapa anterior. Colocamos esse texto na variável texto.
        return texto #Se conseguirmos pegar o texto com sucesso, nós o entregamos (retornamos) para quem chamou a função.
    except Exception as e: #Agora, se algo der errado ao tentar abrir a imagem ou pegar o texto dela, vamos lidar com esse problema.
        print(f"Erro ao extrair texto da imagem {caminho_imagem}: {str(e)}") #Neste ponto, nós mostramos uma mensagem de erro que diz qual imagem teve o problema e qual foi o erro.
        return None #retora none caso tenha algum erro


# Função para encontrar números de RG em um texto
def encontrar_rg(texto):
    # Padrão de expressão regular para um RG brasileiro
    padrao_rg = r"\b\d{2}\.\d{3}\.\d{3}-\d{1,2}\b"

    # Procura por correspondências no texto
    rg_encontrados = re.findall(padrao_rg, texto)

    return rg_encontrados


# Diretório onde as imagens estão localizadas (mude para o seu diretório de imagens)
diretorio_imagens = r'E:\\teste'

# Percorre os arquivos no diretório
for arquivo in os.listdir(diretorio_imagens):
    caminho_arquivo = os.path.join(diretorio_imagens, arquivo)

    # Verifica se o arquivo é uma imagem (você pode ajustar os tipos de arquivo conforme necessário)
    if arquivo.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')):

        # Extrai texto da imagem em várias rotações
        resultados_texto = []
        for angulo in [0, 90, 180, 270]:  # Rotações em graus (0, 90, 180, 270)
            imagem_rotacionada = Image.open(caminho_arquivo).rotate(angulo, expand=True)
            caminho_temporario = "temp_image.png"
            imagem_rotacionada.save(caminho_temporario)
            texto_extraido = extrair_texto_de_imagem(caminho_temporario)
            if texto_extraido:
                resultados_texto.append(texto_extraido)
            os.remove(caminho_temporario)  # Remove a imagem temporária

        # Combine os resultados da extração de texto de todas as rotações
        texto_completo = " ".join(resultados_texto)

        if texto_completo:
            # Encontra RGs no texto completo
            rgs = encontrar_rg(texto_completo)


            if rgs:
                print(f"RG(s) encontrado(s) no arquivo {arquivo}:")
                for rg in rgs:
                    print(rg)
                RG_lista.append(rg)
            else:
                print(f"Nenhum RG encontrado no arquivo {arquivo}")
        else:
            print(f"Não foi possível extrair texto do arquivo {arquivo}")

print(RG_lista)
