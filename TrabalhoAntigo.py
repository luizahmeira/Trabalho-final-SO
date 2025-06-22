import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
from cachetools import cached, LRUCache, TTLCache
from cachetools import LRUCache
from customtkinter import CTkLabel
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import defaultdict
import mimetypes
from datetime import datetime
import threading

#===========================CONFIGURRAÇÕES DE APARÊNCIA===========================
'''#importando aqui os nossos icones de pasta e arquivo pra ficar bem bonitinha a árvore de arquivos'''
#icone_arquivo = CTkImage(Image.open("img_arquivo.png"), size=(16, 16))
#icone_pasta = CTkImage(Image.open("img_pasta.png"), size=(16, 16))

'''setando as aparencias da nossa aplicação! escolhi o dark mode igual ao moço do vídeo'''
def definindo_aparencia():
    ctk.set_appearance_mode("dark") #modo escuro
    ctk.set_default_color_theme("dark-blue") #tema azul escuro

'''criando a janelinha da aplicação! fiz ela parecendo um pop up pq acho mais bonitinho, mas já fiz a aplicação da recursividade também'''
def criando_janela_programa():
    app = ctk.CTk()
    app.title('FreeFileSize')
    app.geometry('1400x1000')
    return app

'''criando nosso frame que vai conter os arquivos do sistema'''
def criando_frame_scroll():
    return ctk.CTkScrollableFrame(master=app, width=375, height=520, fg_color="gray20")  

'''funçãozinha para criar frames com a mesma configuração padrão da aplicação'''
def criar_frame(app, width_value, height_value, fg_color='gray20'):
    return ctk.CTkFrame(master=app, width=width_value, height=height_value, fg_color=fg_color, corner_radius=10)

'''criando o título da nossa aplicação que vai ficar disponível acima do tree file e da barra de pesquisa'''
def criar_titulo(app, titulo, tamanho_fonte, fonte_bold, x, y, coordenadas):
    titulo = ctk.CTkLabel(master=app, text=titulo, font=ctk.CTkFont(size=tamanho_fonte, weight=fonte_bold))
    titulo.place(relx=x, rely=y, anchor=coordenadas)

'''criando o frame da barra de pesquisa'''
def criando_barra_pesquisa(app):
    search_frame = ctk.CTkFrame(master=app, width=250, height=50, fg_color="gray15", corner_radius=8)
    entrada = ctk.CTkEntry(master=search_frame, placeholder_text="Pesquisar por arquivos...", width=200)
    entrada.pack(padx=10, pady=10)
    return search_frame, entrada

'''colocando os frames na tela'''
def place_frames(frame_tree, frame_list, frame_search, frame_pizza):
    frame_search.place(relx=0.03, rely=0.07, anchor='nw') #norte e oeste
    frame_tree.place(relx=0.03, rely=0.18, anchor='nw')  #norte e oeste
    frame_list.place(relx=0.99, rely=0.07, anchor='ne')  #norte e leste
    frame_cache.place(relx=0.99, rely=0.97, anchor='se')  #sul e leste
    frame_pizza.place(relx=0.5, rely=0.5, anchor='center') #centro

#=====================COLOCANDO AS CONFIGURAÇÕES DE APARENCIA==================

'''Definindo a aparência do sistema e criando a nossa janela (app)'''
definindo_aparencia()
app = criando_janela_programa()

'''definindo varivael e lista global para busca de arquivos'''
global entrada_pesquisa
global todos_os_arquivos_do_sistema #luiza aqui
global cache_professor
todos_os_arquivos_do_sistema = []

'''Definindo os frames da nossa tela'''
frame_tree = criando_frame_scroll()
frame_search, entrada_pesquisa = criando_barra_pesquisa(app)
frame_list = ctk.CTkScrollableFrame(master=app, width=400, height=350, fg_color="gray20", corner_radius=10)
frame_cache = ctk.CTkScrollableFrame(master=app, width=400, height=225, fg_color="gray20", corner_radius=10)
#frame_cache = criar_frame(app, 422, 225) 
frame_pizza = criar_frame(app, 400, 400)

'''Travando os frames no tamanho que foram setados, pq se não eles ficam aumentando e diminuindo de tamanho de acordo com o texto'''
#frame_list.pack_propagate(False)
#frame_cache.pack_propagate(False)

'''Colocando os frames definidos na tela em seus devidos lugares'''
place_frames(frame_tree, frame_list, frame_search, frame_pizza)

'''Colocando o título da aplicação na tela'''
criar_titulo(app, "Árvore de arquivos do sistema", 16, "bold", 0.03, 0.01, 'nw')
criar_titulo(app, "Diretórios adicionados ao cache", 16, "bold", 0.88, 0.66, 'se')
criar_titulo(app, "Lista de arquivos do tópico", 16, "bold", 0.86, 0.02, 'ne')

entrada_pesquisa.bind("<Return>", lambda event: pesquisar_arquivo()) #chamado na entrada do tkinder

#===========================CACHE E ARQUIVOS===========================

'''exibindos os arquivos armazenados no cache dentro do frame_cache'''
def mostrar_arquivos_guardados_cache():

    def abrir_popup():
        popup = ctk.CTkToplevel()
        popup.title("Arquivos no Cache")
        popup.geometry("800x400")
        popup.configure(fg_color="gray10")

        #fazendo o cabeçalho para armazenar os caminhos e os timestamps 
        cabecalho_path = ctk.CTkLabel(popup, text="Caminho do Arquivo", text_color="white", anchor="w", font=("Arial", 12, "bold"))
        cabecalho_timestamp = ctk.CTkLabel(popup, text="Timestamp", text_color="white", anchor="w", font=("Arial", 12, "bold"))

        #fazenendo as grids
        cabecalho_path.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        cabecalho_timestamp.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        #adicionando os caminhos (paths) e os timestamps na grid
        for i, path in enumerate(sorted(dir_cache), start=1):
            timestamp = dir_cache_timestamps.get(path)
            if timestamp:
                hora_formatada = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            else:
                hora_formatada = "Não foi cadastrado o timestamp na inclusão ao cache"

            dado_path = ctk.CTkLabel(popup, text=path, text_color="white", anchor="w", wraplength=500)
            dado_timestamp = ctk.CTkLabel(popup, text=hora_formatada, text_color="white", anchor="w")

            #colocando as linhas(rows)
            dado_path.grid(row=i, column=0, sticky="w", padx=10, pady=2)
            dado_timestamp.grid(row=i, column=1, sticky="w", padx=10, pady=2)

    #vamos limpar os dados já presentes no frame para não haver duplicação dos dados
    for widget in frame_cache.winfo_children():
        widget.destroy()

    #para cada path dentro do dir_cache, vamos lista-los com seus nomes, caminhos e hora de inclusão no cache
    for path in sorted(dir_cache):    
        btn = ctk.CTkButton(
            master=frame_cache,
            text=f"{os.path.basename(path)}",
            text_color="white",
            fg_color="gray15",
            hover_color="gray25",
            anchor="w",
            command=abrir_popup
        )
        btn.pack(fill='x', padx=5, pady=2)
    frame_list.update_idletasks()

#=======================BARRA PESQUISA===================================

'''Função que vai buscar os arquivos na barra de pesquisa'''
def pesquisar_arquivo():
    termo = entrada_pesquisa.get().strip().lower() #pega o texto da entrada do frame de pesquisa
    if not termo: #se for vazio, nao retorna nada e sai da função
        return

    #pegar o dicionario que armazena todos os paths que foram abertos no sistema e busca pelo nome do termo pesquisado
    encontrados = [p for p in armazenar_todos_paths if termo in os.path.basename(p).lower()]
    
    #se não houver nenhum narquivo com o termo pesquisado ele limpa o frame da lista e coloca o aviso de que nenhum arquivo foi encontrado
    if not encontrados:
        for widget in frame_list.winfo_children():
            widget.destroy()
        label = ctk.CTkLabel(frame_list, text="Nenhum arquivo encontrado", text_color="white")
        label.pack()
        return #se nao encontrar nenhuma arquivo ele vai embora qui

    #pra cada path na lista dos paths encontrados
    for path in encontrados:
        nome = os.path.basename(path)
        if os.path.isdir(path):
            continue  # ignorar diretórios na pesquisa

        # se o pai ainda não estiver no cache, adiciona
        pai = os.path.dirname(path) #pega só o nome do arquivo
        if pai not in dir_cache: #se o pai não estiver no dir cache, ele adiciona o dir cache
            filhos = listando_filhos(pai) #lista os filhos do caminho
            dir_cache[pai] = filhos #adiicona o path pai e seus filhos ao dir cache
            dir_cache_timestamps[pai] = datetime.now() #adiciona o timestamp no cache
            atualizar_contagem_pizza(pai, filhos) #atualiza contagem da pizza

    plot_pizza_chart(frame_pizza)  #atualiza o gráfico com os novos dados

    #mostra os arquivos encontrados no frame_list
    for widget in frame_list.winfo_children():
        widget.destroy()

    for path in encontrados:
        nome = os.path.basename(path)
        btn = ctk.CTkButton(
            master=frame_list,
            text=nome,
            text_color="white",
            fg_color="gray15",
            hover_color="gray25",
            anchor="w",
            command=lambda p=path: abrir_arquivo(p)
        )
        btn.pack(fill='x', padx=5, pady=2)
    frame_list.update_idletasks()
    

#=============================CACHE CONFIG===============================
'''O objetivo aqui com os caches é evitar ao máximo o reprocessamento dos arquivos os diretórios clicados
para que nossa aplicação não se torne lenta e obsoleta. Então sempre que for clicado em um diretorio do frame_tree
será verificado se esse path desse diretório clicado já não se encontra dentro do cache, pois se já está no cache, não é
necessário ler novamente os arquivos dentro desse path, ou recoloca-lo no cache, pois ele já se encontra lá'''

'''cache que vai armazenar o conteúdo completo dos diretorios'''
dir_cache = LRUCache(maxsize=300)  #cache que vai armazenar os 300 diretórios mais recentes

'''dicionário auxiliar para armazenar o horário de inserção de cada path no dir_cache'''
dir_cache_timestamps = {}

'''armazenar todos os paths que são abertos ao clicar em um arquivo do frame_tree'''
armazenar_todos_paths = set()

'''armazenar paths e seus respectivos tipos para serem listados na lista'''
arquivo_tipo_path = defaultdict(list)  

#print(dir_cache)  #LRUCache({}, maxsize=300, currsize=0)
#print(armazenar_todos_paths) #set()
#print(arquivo_tipo_path) #defaultdict(<class 'list'>, {})

#=============================TREEFILE===============================

'''arrumando o nome do arquivo quando eles forem muito longos'''
def arrumar_nomes_grandes(name, max_length=30):
    if len(name) > max_length:
        return name[:max_length] + "..."  
    else:
        return name

'''função que vai fechar os filhos do arquivo clicado'''
def fechar_filhos(caminho):
    if caminho in paths_botoes:  #verifica se o caminho está entre os botões to frame_tree
        btn = paths_botoes[caminho]
        btn.destroy() #detroy o botão
        del paths_botoes[caminho] #remove o botão dos paths botoes

    if caminho in arquivos_expandidos: #verifica se o caminho está entre um dos arquivos expandidos no frmae_tree
        filhos = listando_filhos(caminho) #pega os filhos do caminho para fechar os botões dos filhos e removelhos dos arquivos expandidos
        for filho in filhos:
            fechar_filhos(filho['caminho']) #passa o caminho do filho como parametro 
        del arquivos_expandidos[caminho] #remove o arquivo dos arquivos expandidos

'''listar os filhos do caminho passado'''
def listando_filhos(caminho):
    try:
        if caminho in dir_cache: #verificar se o arquivo já está no cache
            print(f"[Cache] Retornando itens de {caminho}") 
            return dir_cache[caminho] #caso o caminho clicado já esteja no cache, ele vai apenas retornar os filhos já guardados no chave com o valor do caminho passado
        
        itens = os.listdir(caminho) #caso não esteja no cache, ele vai escanear o caminho e guardar todos os filhos em itens
        lista_completa = []

        for item in sorted(itens, key=str.lower):
            caminho_completo = os.path.join(caminho, item) #fazendo o path do item filho
            armazenar_todos_paths.add(caminho_completo) #adiiconando a lista de todos os paths

            if os.path.isdir(caminho_completo):
                tipo = "diretorio" 
            else:
                tipo = "arquivo"

            lista_completa.append({
                "nome": item,
                "caminho": caminho_completo,
                "tipo": tipo
            }) #lista completa dos filhos do caminho clicado

        return lista_completa

    except PermissionError: #tratando os erros de permissão que eu estava tendo
        text_error = ctk.CTkLabel(
            master=app, 
            text="Usuário não possui permissão para acessar arquivo!", 
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="red"
        )
        text_error.place(relx=0.03, rely=0.97, anchor='sw')
        app.after(5000, text_error.destroy)
        return []
    except Exception as e:
        print(f"Erro: {e}")
        return []

'''função para abrir os filhos do arquivo clicado'''
def abrir_filhos(caminho, botao_referencia, nivel=1):
    if caminho in arquivos_expandidos: #verifica se o arquivo cliicado já não estava expandido, caso estivesse, ele fecha
        filhos = listando_filhos(caminho) #pegar os filhos do arquivo clicado
        for filho in filhos:
            fechar_filhos(filho['caminho']) #fecha os botoes dos filhos
        del arquivos_expandidos[caminho] #remove o caminho dos arquivos expandidos
        return
    
    

    filhos = listando_filhos(caminho) #obtém os filhos (usando cache automático em listando_filhos)

    if caminho not in dir_cache: #verifica se o arquivo já não está no cache antes de adiciona-lo
        dir_cache[caminho] = filhos #adiciona o caminho como chave e os filhos do caminho como valor
        dir_cache_timestamps[caminho] = datetime.now() #adiciona um timestamp para ficar visivel ao professor a hora que foi adicionado o caminho ao cache
        atualizar_contagem_pizza(caminho, filhos)  #atualiza contagem só com os novos filhos

    mostrar_arquivos_guardados_cache() #atualiza o frame que mostra os arquivos adicionados ao cache
    plot_pizza_chart(frame_pizza) #atualiza o nosso grafico de pizza com os novos dados do dir_cache
    anterior = botao_referencia #mantém a referência do botão anterior para posicionar corretamente os novos

    for filho in filhos:
        space = "   " * nivel
        btn = ctk.CTkButton(
            master=frame_tree,
            text=arrumar_nomes_grandes(space + filho['nome']), 
            #image=icone_arquivo if filho['tipo'] == "diretorio" else icone_pasta,
            compound="left", #icone na esquerda do texto
            fg_color="transparent", #botao com fundo transparente
            hover_color="gray25",
            text_color="white",
            anchor="w",
            command=lambda i=filho: abrir_filhos(i['caminho'], paths_botoes[i['caminho']], nivel + 1) #quando clica em um filho, abre os filhos
        )
        btn.pack(after=anterior, fill='x', padx=5, pady=(6 if anterior == botao_referencia else 2))
        paths_botoes[filho['caminho']] = btn
        anterior = btn

    arquivos_expandidos[caminho] = True

'''realoizar a contagem dos arquivos no gráfico de pizza'''
def atualizar_contagem_pizza(caminho, filhos):   
    for item in filhos: #para cada filho do caminho clicado vamos ignorar os diretorios
        if item['tipo'] == 'diretorio': #se for diretório passa o loop e ignora ele
            continue

        _, ext = os.path.splitext(item['nome'])
        tipo = ext.lower() if ext else mimetypes.guess_type(item['nome'])[0] or 'sem extensão'

        if item['caminho'] not in arquivo_tipo_path[tipo]: #verifica se o item clicado pertence ao dificnário que guarda os filhos por tipo e caminho
            arquivo_tipo_path[tipo].append(item['caminho']) #se não estiver ainda no dicionário, ele vai adicionar o item ao dicionario, para posteriormente sabermos quais arquivos se encontram no tópico da fatia de pizza
            contagem_tipo_arquivos[tipo] += 1 #adiciona 1 ao tipo de arquivo relacionado ao item, exemplo: [.py] = 2

'''criando o gráfico de pizza'''
def plot_pizza_chart(frame_pizza):
    global pizza_canvas  #guarda a referencia global para o canvas do gráfico, para possível atualização ou limpeza futura

    #remove o gráfico anterior para carregar o novo
    for widget in frame_pizza.winfo_children():
        widget.destroy()

    contagem = dict(contagem_tipo_arquivos)  #copia o dicionário de contagem de arquivos por tipo

    if not contagem:  #se não há dados para exibir
        dado_vazio = ctk.CTkLabel(frame_pizza, text="Nenhum dado para exibir")
        dado_vazio.pack()
        return

    ordenar_itens = sorted(contagem.items(), key=lambda x: x[1], reverse=True) #ordena os tipos de arquivos por quantidade (decrescente) 
    top_10 = ordenar_itens[:10] #e pega os 10 mais frequentes

    extensao = [item[0] for item in top_10] #extrai rótulos (extensões/tipos)
    quantidade = [item[1] for item in top_10] #extrai valores (quantidade) para o gráfico

    figura = Figure(figsize=(7, 7), dpi=100)     #cria a figura do matplotlib
    figura.patch.set_facecolor("#1a1a1a")  #cor de fundo da figura

    ax = figura.add_subplot(111)  #adiciona um único subplot (gráfico de pizza)

    #cria o gráfico de pizza com porcentagens e início em 140º
    fatia, textos, autotextos = ax.pie(
        quantidade, labels=extensao, autopct='%1.1f%%', startangle=140
    )
    ax.axis('equal')  #garantindo que o grafico vai ficar redondoooooooooo

    #ativa a detecção de cliques ("pick") em cada fatia do gráfico
    for w in fatia:
        w.set_picker(True)

    #define a cor dos textos das labels para branco
    for text in textos:
        text.set_color("white")

    #define a cor dos textos de porcentagem para branco
    for autotext in autotextos:
        autotext.set_color("white")

    #cria um dicionário que relaciona cada wedge (fatia) ao seu respectivo tipo de arquivo
    fatia_tipo = {w: tipo for w, tipo in zip(fatia, extensao)}

    # Cria o canvas que renderiza o gráfico no Tkinter
    pizza_canvas = FigureCanvasTkAgg(figura, master=frame_pizza)
    pizza_canvas.draw()
    pizza_canvas.get_tk_widget().pack()

    #função pra quando o usuário clicar em uma fatia
    def clicar_fatia(event):
        fatia = event.artist  #fatia clicada
        tipo = fatia_tipo.get(fatia)  #identifica o tipo associado a fatia
        if tipo:
            mostrar_arquivos_do_tipo(tipo)  #mostra os arquivos daquele tipo no frame_list
            #print(f"Você clicou na fatia: {tipo} ({mostrar_arquivos_do_tipo(tipo)} arquivos)")  # depuração no terminal

    pizza_canvas.mpl_connect("pick_event", clicar_fatia) #conecta o evento de clique no gráfico à função definida


'''função para abrir o arquivo quando ele for clicado no frame list'''
def abrir_arquivo(path):
    try:
        os.startfile(path)
    except Exception as e:
        erro = ctk.CTkLabel(
            master=frame_list,
            text=f"Erro ao abrir: {e}",
            text_color="red"
        )
        erro.pack()
        app.after(5000, erro.destroy)

'''função que vai mostrar os arquivos presentes na fatia da pizza'''
def mostrar_arquivos_do_tipo(tipo):
    for widget in frame_list.winfo_children(): #limpando o frame para não haver itens duplicados
        widget.destroy()

    arquivos = arquivo_tipo_path.get(tipo) #pegando os arquivos correspondentes ao tipo de arquivo passado

    if not arquivos: #se não houver arquivos, retorna que não tiveram arquivos encontrados
        label = ctk.CTkLabel(frame_list, text="Nenhum arquivo encontrado", text_color="white")
        label.pack()
        return

    for path in arquivos: #lista os arquivos encontrados
        nome = os.path.basename(path)
        btn = ctk.CTkButton(
            master=frame_list,
            text=f"{nome}",
            text_color="white",
            fg_color="gray15",
            hover_color="gray25",
            anchor="w",
            command=lambda p=path: abrir_arquivo(p)
        )
        btn.pack(fill='x', padx=5, pady=2)
    frame_list.update_idletasks()

    return arquivos


#=======================COMEÇANDO CÓDIGO=============================

'''armazzenando os arquivos expandidos para saber quais precisam ser fechados, a chave vai ser o caminho do arquivo e o valor é true! pois ele vai estar expandido'''
arquivos_expandidos = {}

'''armazenando a referencia dos botões com os seus respectivos caminhos (paths), para saber quais botoes destruir quando fechar um arquivo'''
paths_botoes = {}

'''armazena os arquivos por tipo e seus paths'''
arquivo_tipo_path.clear() 

'''armazena a contagem para o gráfico de pizza'''
contagem_tipo_arquivos = defaultdict(int)

#começamos pegando o conteúdeo dentro do diretório C:
for item in listando_filhos("C:\\"):
    if item['tipo'] == "diretorio":
        btn = ctk.CTkButton(
            master=frame_tree,
            text=item['nome'],
            fg_color="transparent",
            hover_color="gray25",
            text_color="white",
            anchor="w",
            command=lambda i=item: abrir_filhos(i['caminho'], paths_botoes[i['caminho']])
        )
        btn.pack(fill='x', padx=5, pady=3)
        paths_botoes[item['caminho']] = btn
        

app.mainloop()

#===========================COISAS A FAZER===========================
'''
aba de pesquisa funcionar
-ao pesquisar por um arquivo, exemplo: %teste.py, ele precisa pegar o path desse cara
-adicionar ele no cache dos filhos
-e recalcular o gráfico de pizza
-sempre que adiciona um cara no cache, é pro gráfico de pizza dar um refresh

fazer a barra de pesquisa que eu ainda nao fiz
'''
