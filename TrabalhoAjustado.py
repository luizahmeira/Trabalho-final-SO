import os
import json
import mimetypes
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
from diskcache import Cache
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
    frame_pizza.place(relx=0.5, rely=0.5, anchor='center') #centro
    
#=============================CACHE==============================================

'''O objetivo aqui com os caches é evitar ao máximo o reprocessamento dos arquivos os diretórios clicados
para que nossa aplicação não FIQUE lenta. Então sempre que for clicado em um diretorio do frame_tree
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

'''armazzenando os arquivos expandidos para saber quais precisam ser fechados, a chave vai ser o caminho do arquivo e o valor é true! pois ele vai estar expandido'''
arquivos_expandidos = {}

'''armazenando a referencia dos botões com os seus respectivos caminhos (paths), para saber quais botoes destruir quando fechar um arquivo'''
paths_botoes = {}

'''armazenar o valor da entrada da pesquisa'''
global entrada_pesquisa

'''armazena os arquivos por tipo e seus paths'''
arquivo_tipo_path.clear() 

'''armazena a contagem para o gráfico de pizza'''
contagem_tipo_arquivos = defaultdict(int)

'''criar um cache que persiste mesmo após o fechamento do programa para armazenar os dados de todos os arquivos filhos do caminho passado
+ armazenar também o timestamp de quando foi feito o escaneamento
pensei em fazer da seguinte forma: escaneia  o caminho passado, guarda no cache sendo: chave(caminho): valor(filhos do caminho)
ai passa para o proximo nivel, pegando os filhos do caminho, setando ele como chave e valor os filhos dele, e assim por diante, até varrer tudo'''
cache_disk = Cache("cache_professor")  #cria ou usa a pasta cache_professor automaticamente
cache_contagem = Cache("cache_contagem")  #novo cache persistente para guardar as contagens
cache_tipo_arquivos = Cache("cache_tipo_arquivos")  #novo cache para tipo -> arquivos
cache_persistente = Cache('cache_arquivos')


'''
{
  "C:/Users/Luiza/Desktop": {
    "arquivos": ["arquivo1.txt", "imagem.png"],
    "pastas": ["subpasta1", "subpasta2"],
    "timestamp": "2025-06-18 22:00:00"
  },
'''

#==========================CONFIGURAÇÕES DE APARENCIA============================

'''Definindo a aparência do sistema e criando a nossa janela (app)'''
definindo_aparencia()
app = criando_janela_programa()

'''Definindo os frames da nossa tela'''
frame_tree = criando_frame_scroll()
frame_search, entrada_pesquisa = criando_barra_pesquisa(app)
frame_list = ctk.CTkScrollableFrame(master=app, width=400, height=600, fg_color="gray20", corner_radius=10)
frame_pizza = criar_frame(app, 400, 400)

'''Colocando os frames definidos na tela em seus devidos lugares'''
place_frames(frame_tree, frame_list, frame_search, frame_pizza)

'''Colocando o título da aplicação na tela'''
criar_titulo(app, "Árvore de arquivos do sistema", 16, "bold", 0.03, 0.01, 'nw')
criar_titulo(app, "Lista de arquivos do tópico", 16, "bold", 0.86, 0.02, 'ne')

entrada_pesquisa.bind("<Return>", lambda event: pesquisar_arquivo()) #chamado na entrada do tkinder

#=======================BARRA PESQUISA===================================

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

'''função para pesquisar o termo digitado na barra de pesquisa dentro do cache_disk'''
def pesquisar_arquivo():
    termo = entrada_pesquisa.get().strip().lower()  #dado digitado na barra de pesquisa
    if not termo: #se for vazio nem faz a pesquisa
        return

    encontrados = [] #guarda os caminhos encontrados durante a pesquisa

    for caminho in cache_disk.iterkeys(): #busca entre todos os caminhos armazenados 
        dados = cache_disk.get(caminho, {}) #carrega od dados da chave do cache_disk que é o caminho 
        arquivos = dados.get("arquivos", []) #e pega todos os arquivos que foram armazenados nessa key com o caminho (ou seja, pega todos os arquivos filhos do caminho)

        for arquivo in arquivos: #loop em todos os arquivos do caminho chave
            if termo in arquivo.lower(): #verifica se o termo está entre a string dos arquivos filhos
                caminho_completo = os.path.join(caminho, arquivo) #monta o caminho completo usando o caminho chave + nome do arquivo para podermos abrir ele futuramente no frame_list
                encontrados.append(caminho_completo) #adiciona o arquivo encontrado a lista de arquivos encontrados

    for widget in frame_list.winfo_children(): #limpando o frame list para evitar dados duplicados de uma pesquisa anterior
        widget.destroy() 

    if not encontrados: #se n encontrar nenhum resultado, informa com um texto no frame list que nada foi encontrado
        label = ctk.CTkLabel(frame_list, text="Nenhum arquivo encontrado com esse termo", text_color="white") 
        label.pack()
        return #e sai da função pq n tem mais nada pra fazer nesse caso

    for path in encontrados: #colocar os resultados no frame_list
        nome = os.path.basename(path) #pegando o nome do arquivo encontrado para usa-lo como nome do botao
        btn = ctk.CTkButton( #criando o botao
            master=frame_list,
            text=nome,
            text_color="white",
            fg_color="gray15",
            hover_color="gray25",
            anchor="w",
            command=lambda p=path: abrir_arquivo(p) #quando clicar no botao com o nome do arquivo, o arquivo será aberto
        )
        btn.pack(fill='x', padx=5, pady=2)

    frame_list.update_idletasks() #dando um update no frame_list


#=============================CACHE PERSISTENTE==============================================

def escanear_e_contar(caminho_inicial):
    '''Escaneia recursivamente, salva no cache_disk e conta tipos de arquivos'''

    contagem_tipo_arquivos.clear()
    arquivo_tipo_path.clear()
    pastas_processadas = set()
    fila = [caminho_inicial]

    while fila:
        caminho_atual = fila.pop(0)

        if caminho_atual in pastas_processadas:
            continue
        pastas_processadas.add(caminho_atual)

        tipo_para_arquivos = defaultdict(list)
        filhos_arquivos = []
        filhos_pastas = []

        try:
            for item in os.listdir(caminho_atual):
                item_caminho = os.path.join(caminho_atual, item)

                if os.path.isfile(item_caminho):
                    _, ext = os.path.splitext(item)
                    tipo = ext.lower() if ext else mimetypes.guess_type(item)[0] or 'sem_extensao'

                    tipo_para_arquivos[tipo].append(item_caminho)
                    arquivo_tipo_path[tipo].append(item_caminho)
                    contagem_tipo_arquivos[tipo] += 1
                    filhos_arquivos.append(item)

                elif os.path.isdir(item_caminho):
                    filhos_pastas.append(item)
                    fila.append(item_caminho)

            dados = dict(tipo_para_arquivos)
            dados["pastas"] = filhos_pastas
            cache_persistente[caminho_atual] = dados

            cache_disk[caminho_atual] = {
                "arquivos": filhos_arquivos,
                "pastas": filhos_pastas,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            print(f"Erro ao escanear {caminho_atual}: {e}")
            continue

    cache_contagem[caminho_inicial] = {
        "contagem": dict(contagem_tipo_arquivos),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"Escaneamento + contagem concluídos e salvos para '{caminho_inicial}'.")

#===================================CONTAGEM PIZZA==========================================

def atualizar_contagem_pizza(caminho_inicial):
    contagem_tipo_arquivos.clear()
    arquivo_tipo_path.clear()
    pastas_processadas = set()
    fila = [caminho_inicial]

    if caminho_inicial in cache_contagem:
        contagem_salva = cache_contagem[caminho_inicial].get("contagem", {})
        contagem_tipo_arquivos.update(contagem_salva)

        while fila:
            caminho_atual = fila.pop(0)

            if caminho_atual in pastas_processadas or caminho_atual not in cache_disk:
                continue
            pastas_processadas.add(caminho_atual)

            dados = cache_disk.get(caminho_atual, {})
            arquivos = dados.get("arquivos", [])
            subpastas = dados.get("pastas", [])

            for nome_arquivo in arquivos:
                _, ext = os.path.splitext(nome_arquivo)
                tipo = ext.lower() if ext else mimetypes.guess_type(nome_arquivo)[0] or 'sem extensão'
                caminho_completo = os.path.join(caminho_atual, nome_arquivo)

                if caminho_completo not in arquivo_tipo_path[tipo]:
                    arquivo_tipo_path[tipo].append(caminho_completo)

            for sub in subpastas:
                caminho_sub = os.path.join(caminho_atual, sub)
                fila.append(caminho_sub)

        return

    while fila:
        caminho_atual = fila.pop(0)

        if caminho_atual in pastas_processadas:
            continue
        pastas_processadas.add(caminho_atual)

        if caminho_atual not in cache_disk:
            continue

        dados = cache_disk[caminho_atual]
        arquivos = dados.get("arquivos", [])
        subpastas = dados.get("pastas", [])

        for nome_arquivo in arquivos:
            _, ext = os.path.splitext(nome_arquivo)
            tipo = ext.lower() if ext else mimetypes.guess_type(nome_arquivo)[0] or 'sem extensão'
            caminho_completo = os.path.join(caminho_atual, nome_arquivo)

            if caminho_completo not in arquivo_tipo_path[tipo]:
                arquivo_tipo_path[tipo].append(caminho_completo)
                contagem_tipo_arquivos[tipo] += 1

        for sub in subpastas:
            fila.append(os.path.join(caminho_atual, sub))

    cache_contagem[caminho_inicial] = {
        "contagem": dict(contagem_tipo_arquivos),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def obter_arquivos_recursivos(caminho_inicial, tipo):
    arquivos = []
    fila = [caminho_inicial]

    while fila:
        caminho_atual = fila.pop(0)
        dados = cache_persistente.get(caminho_atual, {})
        arquivos += dados.get(tipo, [])

        for sub in dados.get("pastas", []):
            caminho_sub = os.path.join(caminho_atual, sub)
            fila.append(caminho_sub)

    return arquivos

'''função que vai mostrar os arquivos presentes na fatia da pizza'''
def mostrar_arquivos_do_tipo(caminho, tipo):
    for widget in frame_list.winfo_children():
        widget.destroy()

    arquivos = obter_arquivos_recursivos(caminho, tipo)

    if not arquivos:
        label = ctk.CTkLabel(frame_list, text="Nenhum arquivo encontrado", text_color="white")
        label.pack()
        return
    
    contador = 0

    for path in arquivos:

        if contador >= 100:
            break

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

        contador += 1

    frame_list.update_idletasks()
    return arquivos

def plot_pizza_chart(frame_pizza, caminho_atual):
    global pizza_canvas  #referencia global para o canvas do gráfico

    #remove o gráfico anterior para recarregar
    for widget in frame_pizza.winfo_children():
        widget.destroy()

    #se caminho_atual é informado, tenta buscar a contagem no cache_analise
    if caminho_atual and caminho_atual in cache_contagem:
        contagem = cache_contagem[caminho_atual].get("contagem", {})
    else:
        #senão, usa o contagem_tipo_arquivos atual em memória
        contagem = dict(contagem_tipo_arquivos)

    if not contagem:
        label_vazio = ctk.CTkLabel(frame_pizza, text="Nenhum dado para exibir")
        label_vazio.pack()
        return

    ordenar_itens = sorted(contagem.items(), key=lambda x: x[1], reverse=True)
    top_10 = ordenar_itens[:10]

    extensao = [item[0] for item in top_10]
    quantidade = [item[1] for item in top_10]

    figura = Figure(figsize=(7, 7), dpi=100)
    figura.patch.set_facecolor("#1a1a1a")

    ax = figura.add_subplot(111)

    fatia, textos, autotextos = ax.pie(
        quantidade, labels=extensao, autopct='%1.1f%%', startangle=140
    )
    ax.axis('equal')

    for w in fatia:
        w.set_picker(True)

    for text in textos:
        text.set_color("white")

    for autotext in autotextos:
        autotext.set_color("white")

    fatia_tipo = {w: tipo for w, tipo in zip(fatia, extensao)}

    pizza_canvas = FigureCanvasTkAgg(figura, master=frame_pizza)
    pizza_canvas.draw()
    pizza_canvas.get_tk_widget().pack()

    def clicar_fatia(event):
        fatia = event.artist
        tipo = fatia_tipo.get(fatia)
        if tipo:
            mostrar_arquivos_do_tipo(caminho_atual, tipo)

    pizza_canvas.mpl_connect("pick_event", clicar_fatia)

#===================================TREE FILE===============================================

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

    def clicando_caminho(caminho):
        def escaner():
            if caminho in cache_contagem:
                app.after(0, lambda: plot_pizza_chart(frame_pizza, caminho))
                return
            
            escanear_e_contar(caminho)

            if caminho in cache_contagem: #atualiza gráfico na thread principal
                atualizar_contagem_pizza(caminho)
                app.after(0, lambda: plot_pizza_chart(frame_pizza, caminho))
                return

        threading.Thread(target=escaner, daemon=True).start()
        
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
            command=lambda i=filho: (
                abrir_filhos(i['caminho'], paths_botoes[i['caminho']], nivel + 1),
                clicando_caminho(i['caminho'])
            ) #quando clica em um filho, abre os filhos
        )
        btn.pack(after=anterior, fill='x', padx=5, pady=(6 if anterior == botao_referencia else 2))
        paths_botoes[filho['caminho']] = btn
        anterior = btn

    arquivos_expandidos[caminho] = True

#=============================MAIN===========================================================
def main():

    '''função para printar o cache_disk que é o cache persistente que o professor pediu para que implementassemos até domingo'''
    def imprimir_cache_disk():
        print("\n=== Conteúdo do cache_disk ===") #faz um cabeçalho fofinho
        for caminho in cache_disk.iterkeys():  # iterando sobre as chaves
            dados = cache_disk.get(caminho, {}) #busca os dados do caminho (chave do cache_disk) 
            print(f"\nCaminho: {caminho}") #printa o caminho do arquivo chave armazenado
            print(f"Arquivos: {dados.get('arquivos', [])}") #printa os arquivos filhos do caminho
            print(f"Pastas: {dados.get('pastas', [])}") #printa s pastas filhos do caminho
            print(f"Timestamp: {dados.get('timestamp', 'Sem timestamp')}") #e printa o timestamp, que foi o momento da inclusão
        print("=== Fim do conteúdo ===\n") #demarca o fim do conteúdo do caminho (chave) do cache_disk

    '''função que vai limpar o cache_disk'''
    def limpar_cache_disk():
        cache_disk.clear() #dando um clear no cache
        cache_contagem.clear()
        cache_tipo_arquivos.clear()
        cache_persistente.clear()
        dir_cache.clear()
        print("caches limpos com sucesso.")

    frame_botoes_cache_disk = ctk.CTkFrame(master=app, width=400, height=60, fg_color="gray15")
    frame_botoes_cache_disk.place(relx=0.5, rely=0.9, anchor='center') #colocando o frame com os botões com as ações de printar e limpar

    btn_print_cache = ctk.CTkButton( #criando o botão de print
        master=frame_botoes_cache_disk,
        text="Printar cache",
        command=imprimir_cache_disk,
        fg_color="gray25",
        hover_color="gray35",
        text_color="white"
    )
    btn_print_cache.pack(side="left", padx=10, pady=10) #colocando o botão

    btn_limpar_cache = ctk.CTkButton( #criando o botão de limpar o cache
        master=frame_botoes_cache_disk, 
        text="Limpar cache",
        command=limpar_cache_disk,
        fg_color="darkred",
        hover_color="red",
        text_color="white"
    )
    btn_limpar_cache.pack(side="left", padx=10, pady=10) #colocando o botão

    label_status = ctk.CTkLabel(
        master=app,
        text="",  #começa vazio
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color="white"
    )
    label_status.place(relx=0.5, rely=0.1, anchor="s")  #acima do gráfico


    '''função com thread que vai começar a escanear todo o arquivo clicado'''
    def clicando_caminho(caminho):
        def escaner():
            app.after(0, lambda: label_status.configure(text="Escaneando diretório, por favor aguarde..."))

            if caminho in cache_contagem:
                app.after(0, lambda: plot_pizza_chart(frame_pizza, caminho))
                app.after(0, lambda: label_status.configure(text=""))
                return

            escanear_e_contar(caminho)

            if caminho in cache_contagem:
                atualizar_contagem_pizza(caminho)
                app.after(0, lambda: plot_pizza_chart(frame_pizza, caminho))

            app.after(0, lambda: label_status.configure(text=""))  #limpa no fim

        threading.Thread(target=escaner, daemon=True).start()

    '''começamos pegando o conteúdeo dentro do diretório C:'''
    for item in listando_filhos("C:\\"):
        if item['tipo'] == "diretorio":
            caminho = item['caminho']
            btn = ctk.CTkButton(
                master=frame_tree,
                text=item['nome'],
                fg_color="transparent",
                hover_color="gray25",
                text_color="white",
                anchor="w"
            )
            btn.configure(command=lambda c=caminho, b=btn: (abrir_filhos(c, b), clicando_caminho(c))) #configurando os comandos executados ao realizar o click no botão
            btn.pack(fill='x', padx=5, pady=3) #colocando o botão
            paths_botoes[caminho] = btn #colocandoo botão na lista de botões existentes

    app.mainloop()

if __name__ == "__main__":
    main()
