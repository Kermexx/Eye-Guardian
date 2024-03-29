    def graphic(self):
        messagebox.showinfo("DICA",
                            "O gráfico que lista o caminho dos diretórios é separado em cores, onde: Azul - TOP 1, Amarelo - TOP 2, Verde - TOP 3!")
        if not os.path.exists("resultado_scan.xlsx"):
            messagebox.showwarning("Aviso", "O arquivo 'resultado_scan.xlsx' não existe.")
            return

        # Carregando os dados do arquivo Excel
        data = pd.read_excel("resultado_scan.xlsx")

        if data.empty:
            messagebox.showwarning("Aviso", "O arquivo 'resultado_scan.xlsx' está vazio.")
            return

        # Converte as colunas 'Data' e 'Horário' para datetime e combina-as
        data['Data'] = pd.to_datetime(data['Data'].astype(str) + ' ' + data['Horário'].astype(str),
                                      format='%d-%m-%Y %H:%M:%S', dayfirst=True)

        # Ordena os dados pela coluna 'Data' do mais recente para o mais antigo
        data.sort_values(by='Data', ascending=False, inplace=True)

        # Seleciona as linhas com a data mais recente
        latest_time = data['Data'].max()
        latest_data = data[data['Data'] == latest_time]

        # Atualiza o campo 'Diretório' para refletir o caminho da pasta, não do arquivo
        latest_data['Diretório'] = latest_data['Diretório'].apply(lambda x: str(Path(x).parent))

        # Preparando o conjunto de dados com a contagem de informações por diretório
        directory_info_counts = latest_data.groupby('Diretório')['Informação encontrada'].count().sort_values(
            ascending=False)
        top_directories = directory_info_counts.head(3)
        total_info = directory_info_counts.sum()
        directory_percents = (top_directories / total_info) * 100
        other_percent = 100 - directory_percents.sum()

        # Definindo o tamanho da figura
        desired_width_px = 1200
        desired_height_px = 700
        dpi = plt.rcParams.get('figure.dpi')
        figsize_inches = (desired_width_px / dpi, desired_height_px / dpi)
        fig = plt.figure(figsize=figsize_inches, dpi=dpi)

        # Função para quebrar as linhas de texto para as legendas
        def wrap_labels(labels, width=30):
            return ['\n'.join(textwrap.wrap(label, width=width)) for label in labels]

        # Gráfico geral de informações sensíveis encontradas
        total_info_latest = latest_data['Informação encontrada'].value_counts()
        wrapped_labels_total_info = wrap_labels(total_info_latest.index)
        ax1 = fig.add_subplot(2, 2, 2)
        ax1.pie(total_info_latest, labels=wrapped_labels_total_info, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Total de Informações Sensíveis Encontradas - (Todos diretórios)', fontsize=10, fontweight='bold')

        # Gráfico dos TOP 3 diretórios
        pie_labels = ['TOP 1 - ' + top_directories.index[0], 'TOP 2 - ' + top_directories.index[1],
                      'TOP 3 - ' + top_directories.index[2], 'Outros']
        pie_data = pd.concat([directory_percents, pd.Series([other_percent], index=['Outros'])])
        wrapped_labels_pie_data = wrap_labels(pie_labels)

        ax_total_comparison = fig.add_subplot(2, 2, 1)
        ax_total_comparison.pie(pie_data, labels=wrapped_labels_pie_data, autopct='%1.1f%%', startangle=90,
                                labeldistance=1.3)
        ax_total_comparison.set_title('TOP 3 Diretórios mais sensíveis', fontsize=10, fontweight='bold')

        # Gráficos detalhados para cada um dos TOP 3 diretórios
        for i, directory in enumerate(top_directories.index, start=1):
            specific_data = latest_data[latest_data['Diretório'] == directory]
            info = specific_data['Informação encontrada'].value_counts()
            wrapped_labels_info = wrap_labels(info.index)
            ax = fig.add_subplot(2, 3, i + 3)
            ax.pie(info, labels=wrapped_labels_info, autopct='%1.1f%%', startangle=90)
            ax.set_title(f'TOP {i} - Diretório Sensível', fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.show()
