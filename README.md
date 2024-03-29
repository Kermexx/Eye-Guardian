
# Eye Guardian

O Eye Guardian é uma aplicação projetada para escanear diretórios em busca de informações sensíveis, suportando vários formatos de arquivos e fornecendo relatórios esclarecedores.

## Configuração

Antes de executar a aplicação, você precisa instalar as bibliotecas Python necessárias. Execute os seguintes comandos no seu terminal:

```bash
pip install PyMuPDF google-cloud-vision python-docx python-pptx openpyxl Pillow schedule customtkinter pandas matplotlib
```

## Executando a Aplicação

Após instalar as bibliotecas necessárias, você pode rodar a aplicação executando o script Python principal:

```bash
python Código_com_IA.py
```

Substitua `Código_com_IA.py` por 'Código_sem_IA.py' caso prefira usar o app sem a Inteligência Artificial.

## Funcionalidades

- **Escanear Diretórios**: Realize uma varredura detalhada em diretórios selecionados para identificar informações sensíveis.
- **Integração com Outlook**: Baixe e escaneie e-mails e anexos da sua conta Outlook.
- **Geração de Relatórios**: Gere relatórios abrangentes em formatos Excel e gráfico, resumindo as descobertas.
- **Gerenciamento de Arquivos**: Opções para excluir ou mover arquivos sensíveis identificados durante a varredura.
- **Monitoramento de Blacklist**: Monitore continuamente diretórios especificados e alerte sobre qualquer informação sensível.
- **GUI Interativa**: A aplicação vem com uma interface gráfica amigável, facilitando o acesso às suas funcionalidades.

## Uso

1. **Selecionar Diretório**: Escolha o diretório que deseja escanear.
2. **Escolher Chave**: Se for escanear imagens, selecione o arquivo de chave JSON para a API do Google Cloud Vision.
3. **Escanear**: Inicie o processo de varredura para encontrar informações sensíveis dentro do diretório selecionado.
4. **Relatórios**: Acesse os relatórios gerados pelos botões "Relatório Excel" e "Relatório em Gráfico".
5. **Outlook**: Use o botão "Outlook" para escanear seus e-mails do Outlook em busca de informações sensíveis.
6. **Blacklist**: Adicione diretórios à lista negra para monitoramento contínuo.

## Personalização

Você pode modificar os parâmetros de varredura e os tipos de informações sensíveis que a aplicação procura ajustando o código-fonte.

