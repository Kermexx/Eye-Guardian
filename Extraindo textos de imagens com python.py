# Antes de tudo instale no terminal > pip install PyMuPDF
# Antes de tudo instale no terminal > pip install google-cloud-vision
# Antes de tudo instale no terminal > pip install python-docx
# Antes de tudo instale no terminal > pip install python-pptx
# Antes de tudo instale no terminal > pip install openpyxl
# Antes de tudo instale no terminal > pip install Pillow
# Antes de tudo instale no terminal > pip install schedule
# Antes de tudo instale no terminal > pip install customtkinter
import os  # funções para manipular caminhos de arquivos
import re  # ajuda a usar padrões de busca do scan
import shutil  # Copia e/ou move os arquivos
import fitz  # PymuPDF
from google.cloud import vision
from docx import Document  # Para lidar com arquivos DOCX
from pptx import Presentation  # powerpoint
import openpyxl  # Para lidar com arquivos XLSX
import tkinter as tk
# imports de design
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from tkinter import Canvas, Entry, Text, Button, PhotoImage
from pathlib import Path
import sys
from customtkinter import *
from PIL import Image, ImageTk
import time  # contador
import schedule  # contador
import customtkinter as ctk
from tkinter import simpledialog
import json  # transforamar o save em um arquivo JSON
import base64  # para a imagem do design virar base64
import io  # load do save
import csv  # relatório
from datetime import datetime

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
                    matches_genero = re.findall(
                        r'\b(Masculino|masculino|M|Homem|homem|Feminino|feminino|Mulher|mulher|F)\b', cell_value)
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

                    sensitive_info.extend([('CPF', cpf) for cpf in matches_cpf])
                    sensitive_info.extend([('CNPJ', cnpj) for cnpj in matches_cnpj])
                    sensitive_info.extend([('Email', email) for email in matches_email])
                    sensitive_info.extend([('Telefone', telefone) for telefone in valid_telefones])
                    sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
                    # Extrai informações sobre religiões
                    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', cell_value,
                                                             'Religião', sensitive_info)
                    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', cell_value,
                                                             'Cor/Etnia', sensitive_info)
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
        text = "\n".join(
            [shape.text for slide in presentation.slides for shape in slide.shapes if hasattr(shape, "text")])

    else:
        text = pptx_path_or_text

    sensitive_info = []

    # Aplica expressões regulares para encontrar informações sensíveis
    matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-(?:\d{1,2})', text)
    matches_cpf = re.findall(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})', text)
    matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
    matches_email = re.findall(r'\S+@\S+', text)
    matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
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
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião', sensitive_info)
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',
                                             sensitive_info)

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
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião',
                                                 sensitive_info)
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',
                                                 sensitive_info)

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
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião',
                                                 sensitive_info)
        sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',
                                                 sensitive_info)

    # Adiciona as informações sensíveis extraídas ao dicionário de resultados
    if sensitive_info:
        results[image_path] = results.get(image_path, [])
        results[image_path].extend(sensitive_info)

    return results


# Função para extrair informações sensíveis de um arquivo TXT

def extract_sensitive_info_from_txt(txt_path, results):
    with open(txt_path, 'rb') as txt_file:
        text = txt_file.read().decode('utf-8', errors='ignore')  # Decodificar explicitamente como UTF-8

    sensitive_info = []

    # Aplica expressões regulares para encontrar informações sensíveis
    matches_rg = re.findall(r'\d{2}\.\d{3}\.\d{3}-\d{1,2}|\d{8}-\d{1,2}|\d{7,9}-\d{1,2}', text)
    matches_cpf = re.findall(r'\b(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{9}/\d{2}|\d{11})\b', text)
    matches_cnpj = re.findall(r'\d{2}.\d{3}.\d{3}/\d{4}-\d{2}', text)
    matches_email = re.findall(r'\S+@\S+', text)
    matches_telefone = re.findall(r'\(\d{2}\)\d{5}-\d{4}|\(\d{2}\)\d{4,5}-\d{4}', text)
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
    sensitive_info.extend([('Gênero', genero) for genero in matches_genero])
    # Extrai informações sobre religiões
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião', sensitive_info)
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',
                                             sensitive_info)

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
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(religioes) + r'\b', text, 'Religião', sensitive_info)
    sensitive_info = extract_info_by_pattern(r'\b' + r'\b|\b'.join(cores_etnias) + r'\b', text, 'Cor/Etnia',
                                             sensitive_info)

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
caminho_diretorio = ''
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


class MeuApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Eye Guardian")
        self.geometry("1200x700")

        # Variáveis
        self.directory_path = tk.StringVar()
        self.key_path = tk.StringVar()
        self.sensitive_files = []
        self.blacklist_directories = []
        self.scan_reports = []

        # Carregar configurações salvas, se houver
        self.load_settings()

        # Criar e exibir widgets
        self.create_widgets()

        # Definindo o modo de aparência inicial
        ctk.set_appearance_mode("dark")

        # Agendar a execução do escaneamento a cada 5 minutos
        schedule.every(2).minutes.do(self.scan_blacklist_directories)

        # Iniciar o loop de agendamento
        self.after(100, self.start_schedule_loop)

    def create_widgets(self):
        frame = ctk.CTkScrollableFrame(master=self, fg_color="transparent", border_color="#962CCA", border_width=2,
                                       height=600)
        frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10)

        ctk.CTkButton(master=frame, text="Tutorial", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.tutorial).grid(
            row=0, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Escanear", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.start_scan).grid(row=1, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Escolher Diretório", corner_radius=32, fg_color="#0f0913",
                      hover_color="#53DEC9", command=self.choose_directory).grid(row=2, column=0, padx=30, pady=20,
                                                                                 sticky="ew")
        ctk.CTkButton(master=frame, text="Escolher Chave", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.choose_key_file).grid(row=3, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Excluir Arquivos", corner_radius=32, fg_color="#0f0913",
                      hover_color="#53DEC9", command=self.delete_files).grid(row=4, column=0, padx=30, pady=20,
                                                                             sticky="ew")
        ctk.CTkButton(master=frame, text="Mover Arquivos", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.move_files).grid(row=5, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Adicionar Blacklist", corner_radius=32, fg_color="#0f0913",
                      hover_color="#53DEC9", command=self.choose_blacklist_directory).grid(row=6, column=0, padx=30,
                                                                                           pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Salvar", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.save_settings).grid(
            row=10, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Sair", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.close_program).grid(row=11, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Lista Blacklist", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.show_blacklist).grid(row=7, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=frame, text="Relatório", corner_radius=32, fg_color="#0f0913", hover_color="#53DEC9",
                      command=self.open_report).grid(row=9, column=0, padx=30, pady=20, sticky="ew")
        ctk.CTkButton(master=self, text="", width=300, height=50, corner_radius=32, fg_color="#0f0913",
                      hover_color="#53DEC9").grid(row=1, column=1, pady=10)

        # String base64 da imagem
        base64_image = """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"""
        # Decodificar a string de base64 em uma imagem
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        image = ImageTk.PhotoImage(image)

        # Exibir a imagem
        image_label = ctk.CTkLabel(master=self, image=image, text="")
        image_label.grid(row=1, column=1, padx=10, pady=10)
        # Quadrado Vazio
        quadrado_vazio = ctk.CTkFrame(master=self, width=900, height=500, border_color="#962CCA", border_width=2)
        quadrado_vazio.grid(row=2, column=1, padx=10, pady=(0, 60))
        quadrado_vazio.grid_rowconfigure(0, weight=1)
        quadrado_vazio.grid_columnconfigure(0, weight=1)

        self.output_text = ctk.CTkTextbox(master=quadrado_vazio, wrap=tk.WORD, border_color="#962CCA", border_width=1,
                                          height=500, width=900)
        self.output_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def show_blacklist(self):
        blacklist_window = tk.Toplevel(self)
        blacklist_window.title("Lista Blacklist")
        blacklist_window.geometry("800x600")  # Definindo a geometria da janela

        listbox_frame = tk.Frame(blacklist_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True)  # Faz o frame expandir para preencher toda a janela

        listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # Faz a Listbox preencher todo o frame

        for directory in self.blacklist_directories:
            listbox.insert(tk.END, directory)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        def remove_selected():
            selected_indices = listbox.curselection()
            selected_directories = [listbox.get(index) for index in selected_indices]
            for directory in selected_directories:
                self.blacklist_directories.remove(directory)
            messagebox.showinfo("Removido", "Os diretórios selecionados foram removidos da blacklist.")
            self.save_settings()

        def clear_blacklist():
            self.blacklist_directories = []
            messagebox.showinfo("Blacklist Esvaziada", "A lista de blacklist foi esvaziada com sucesso.")

        remove_button = tk.Button(blacklist_window, text="Remover Selecionados", command=remove_selected)
        remove_button.pack(padx=10, pady=10)
        esvaziar_button = tk.Button(blacklist_window, text="Esvaziar Blacklist", command=clear_blacklist)
        esvaziar_button.pack(padx=10, pady=10)

    # save
    def load_settings(self):
        if os.path.exists("settings.json") and os.path.getsize("settings.json") > 0:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.key_path.set(settings.get("key_path", ""))
                if self.key_path.get():
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.key_path.get()
                self.blacklist_directories = settings.get("blacklist_directories", [])
        else:
            messagebox.showwarning("Aviso", "O arquivo de configuração está vazio ou não existe.")

    def save_settings(self):
        settings = {
            "key_path": self.key_path.get(),
            "blacklist_directories": self.blacklist_directories
        }

        with open("settings.json", "w") as f:
            json.dump(settings, f)

        messagebox.showinfo("Salvo", "As configurações foram salvas com sucesso.")

    def tutorial(self):
        popup = tk.Toplevel(self)
        popup.title("Tutorial")
        popup.geometry("800x600")

        scrollbar = tk.Scrollbar(popup)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tutorial_text = tk.Text(popup, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Arial", 12))
        tutorial_text.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=tutorial_text.yview)

        # Adicione o conteúdo do tutorial aqui
        tutorial_content = """
        COMO PEGAR A CHAVE JSON:


 01- Crie uma conta no Google Cloud (cloud.google.com).

02- Adicione a forma que quer que seja feito os pagamentos.

03- Crie um novo Projeto.

04- Após criado, clique nas 3 barrinhas no canto superior esquerdo. Escolha "APIs e serviços" e em seguida "Biblioteca".

05- Pesquise por "Cloud Vision API".

06- Selecione a que se parece com um olho azul.

07- Clique em ativar e recarregue a pagina e verifique se a opção "ativar" mudou para "gerenciar".

08- Clique nas 3 barrinhas no canto superior esquerdo. Escolha "APIs e serviços" e em seguida "Credenciais".

09- Clique em "Criar Credencial" e escolha "Contas de Serviço".

10- Escolha um nome para a conta de serviço e crie.

11- Após isso clique na conta de serviço e vá em "chaves".

12- Clique em "adicionar chave" e crie uma nova chave JSON.

13- Coloque a chave em algum diretório que você irá se lembrar para quando for usar o aplicativo.

        FUNCIONAMENTO DOS BOTÕES:



01- Tutorial > Abre o tutorial (onde você está agora).

02- Escanear > Escaneia o diretório escolhido.

03- Escolher Diretório > Escolhe o diretório a receber o scan.

04- Escolher Chave > Seleciona a chave JSON da I.A dentro do diretório que foi salvo. (necessário para Scan de imagens)

05- Excluir Arquivos > Exclui todos arquivos sensiveis encontrados no diretório escolhido com exceção dos não sensíveis (necessário ter feito o scan antes).

06- Mover Arquivos > Move todos arquivos sensiveis encontrados para um diretório de sua escolha (necessário ter feito o scan antes).

07- Adicionar Blacklist > Escolhe 1 ou mais diretórios para ser constantemente monitorado em busca de arquivos sensiveis, caso algum arquivo sensível apareça será aberto um pop-up falando que foi encontrado um arquivo sensível e te mostrará o diretório que ele se encontra.

08- Lista Blacklist > Mostra a lista de todos diretórios salvos na blacklist, caso queira remover 1 ou mais basta clicar nos desejados e então clicar em "Remover Selecionados".

09- Esvaziar Blacklist > Remove todos diretórios escolhidos para estar na blacklist.

10- Salvar > Salvará suas configurações para a próxima inicialização.

11- Sair > Sairá do aplicativo.
        """

        tutorial_text.tag_configure("bold", font=("Arial", 12, "bold"))
        tutorial_text.insert(tk.END, tutorial_content)

    def choose_key_file(self):
        key_file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if key_file:
            self.key_path.set(key_file)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_file
            self.save_settings()  # Salvar as configurações sempre que o caminho da chave for definido

    def choose_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_path.set(directory)

    def generate_report(self):
        # Abre ou cria um arquivo para o relatório
        with open("scan_report.csv", mode="w", newline="") as report_file:
            report_writer = csv.writer(report_file)

            # Escreve o cabeçalho do relatório
            report_writer.writerow(["Data Scan", "Horário", "Diretório", "Ação Realizada"])

            # Escreve os dados de cada escaneamento
            for scan_data in self.scan_reports:
                data_scan, horario, diretorio, _, acao_realizada = scan_data
                report_writer.writerow([data_scan, horario, diretorio, acao_realizada])

    def open_report(self):
        if os.path.exists("scan_report.csv"):
            os.system("start scan_report.csv")
        else:
            messagebox.showwarning("Aviso", "O relatório ainda não foi gerado.")

    def start_scan(self):
        directory_path = self.directory_path.get()
        if directory_path:
            # Limpa o texto antigo
            self.output_text.delete(1.0, tk.END)

            results = {}
            process_directory(directory_path, results)

            sensitive_files = []

            for path, data in results.items():
                results[path] = list(set(data))
                sensitive_files.append(path)

            for path, data in results.items():
                path = os.path.normpath(path)
                self.output_text.insert(tk.END, f"Informações sensíveis encontradas em: {path}\n")

                types_found = set(info[0] for info in data)
                for info_type in types_found:
                    self.output_text.insert(tk.END, f"{info_type} encontrado\n")

                self.output_text.insert(tk.END, "\n")

            self.sensitive_files = sensitive_files

            # Adiciona os dados do escaneamento a self.scan_reports
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            for path, data in results.items():
                self.scan_reports.append([current_time, directory_path, path, data, "Escaneado"])

            # Gera o relatório
            self.generate_report()

    def delete_files(self):
        directory_path = self.directory_path.get()
        if directory_path:
            confirmation = messagebox.askyesno("Confirmação",
                                               "Tem certeza de que deseja excluir todos os arquivos sensíveis no diretório?")
            if confirmation:
                for sensitive_file in self.sensitive_files:
                    if os.path.isfile(sensitive_file):
                        os.remove(sensitive_file)

                messagebox.showinfo("Concluído", "Todos os arquivos sensíveis foram excluídos com sucesso.")

    def move_files(self):
        if not self.sensitive_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo sensível foi encontrado.")
            return

        destination_directory = filedialog.askdirectory()
        if destination_directory:
            for sensitive_file in self.sensitive_files:
                try:
                    shutil.move(sensitive_file, destination_directory)
                except Exception as e:
                    self.output_text.insert(tk.END, f"Erro ao mover arquivo '{sensitive_file}': {str(e)}\n")

        messagebox.showinfo("Transferência concluída!", "Todos os arquivos foram transferidos com sucesso!")

    def close_program(self):
        self.destroy()  # Fecha a janela principal do aplicativo

    def choose_blacklist_directory(self):
        blacklist_directory = filedialog.askdirectory()
        if blacklist_directory:
            # Salvar o diretório escolhido na lista de diretórios de lista negra
            self.blacklist_directories.append(blacklist_directory)

    def start_schedule_loop(self):
        # Loop para verificar e executar os agendamentos
        self.scan_blacklist_directories()  # Executar imediatamente antes de entrar no loop
        self.after(1000, self.start_schedule_loop)  # Agendar a próxima execução

    def scan_blacklist_directories(self):
        sensitive_files = []
        for directory in self.blacklist_directories:
            results = {}
            process_directory(directory, results)
            for path, data in results.items():
                if data:  # Verifica se há informações sensíveis encontradas
                    path = os.path.normpath(path)
                    sensitive_files.append(path)

        if sensitive_files:
            sensitive_message = "\n".join(f"Informações sensíveis encontradas em: {path}" for path in sensitive_files)
            messagebox.showinfo("Aviso", sensitive_message)


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


if __name__ == "__main__":
    app = MeuApp()
    app.mainloop()
