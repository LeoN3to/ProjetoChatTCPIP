import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import simpledialog
from tkinter import ttk  #emoji
from tkinter import filedialog
import os


def abrir_janela_emojis():
    janela_emojis = tk.Toplevel(janela)
    janela_emojis.title("Selecionar Emoji")
    janela_emojis.configure(bg="#2c2f33")
    janela_emojis.resizable(False, False)

    notebook = ttk.Notebook(janela_emojis)
    notebook.pack(padx=10, pady=10)

    categorias = {
        "Carinhas": ['😀', '😂', '😍', '😢', '😡', '😎'],
        "Gestos": ['👍', '🙏', '👎', '🤙', '👏', '👌'],
        "Símbolos": ['❤️', '💔', '🎉', '💀', '✨', '🔥']
    }

    for nome_categoria, lista_emojis in categorias.items():
        frame = tk.Frame(notebook, bg="#2c2f33")
        notebook.add(frame, text=nome_categoria)

        linha = 0
        coluna = 0
        for emoji in lista_emojis:
            btn = tk.Button(
                frame,
                text=emoji,
                width=4,
                font=("Arial", 14),
                command=lambda em=emoji: inserir_emoji_no_chat(em, janela_emojis)
            )
            btn.grid(row=linha, column=coluna, padx=5, pady=5)
            coluna += 1
            if coluna > 5:
                coluna = 0
                linha += 1

def inserir_emoji_no_chat(emoji, janela_emojis):
    entrada_mensagem.insert(tk.END, emoji)
    janela_emojis.destroy()


# Função para receber mensagens do servidor

def receber_mensagens():
    while True:
        try:
            mensagem = cliente.recv(1024).decode('utf-8')
            if mensagem.startswith("/file:"):
                nome_arquivo = mensagem.split(":", 1)[1]
                dados = cliente.recv(1024 * 1024)
                with open(f"recebido_{nome_arquivo}", "wb") as f:
                    f.write(dados)
                mostrar_mensagem(f"Arquivo recebido: recebido_{nome_arquivo}")
            else:
                mostrar_mensagem(mensagem)
        except:
            mostrar_mensagem("Conexão encerrada.")
            cliente.close()
            break

# Mostrar mensagem na janela

def mostrar_mensagem(mensagem):
    area_texto.config(state='normal')
    area_texto.insert('end', mensagem + '\n')
    area_texto.config(state='disabled')
    area_texto.see('end')

# Enviar mensagem ao servidor

def enviar_mensagem():
    mensagem = entrada_mensagem.get()
    entrada_mensagem.delete(0, 'end')
    if mensagem:
        mensagem_formatada = f"{nome}: {mensagem}"
        mostrar_mensagem(mensagem_formatada)
        cliente.send(mensagem_formatada.encode('utf-8'))

def enviar_arquivo():
    caminho_arquivo = filedialog.askopenfilename()
    if caminho_arquivo:
        try:
            with open(caminho_arquivo, 'rb') as f:
                dados = f.read()
            nome_arquivo = os.path.basename(caminho_arquivo)
            cliente.send(f"/file:{nome_arquivo}".encode('utf-8'))
            cliente.sendall(dados)
            mostrar_mensagem(f"Você enviou o arquivo '{nome_arquivo}'")
        except Exception as e:
            mostrar_mensagem(f"Erro ao enviar arquivo: {e}")


# Criar interface

janela = tk.Tk()
janela.title("Chat TCP/IP")
janela.configure(bg='#2c2f33')  # Fundo escuro

area_texto = scrolledtext.ScrolledText(
    janela, 
    state='disabled', 
    fg='#f1f1f1', 
    bg='#23272a',
    font=('Consolas', 12),
    wrap='word'
)
area_texto.pack(padx=10, pady=10)

entrada_mensagem = tk.Entry(
    janela, 
    width=50, 
    fg='#f1f1f1', 
    bg='#23272a',
    insertbackground='white',  # cor do cursor
    font=('Consolas', 11)
)
entrada_mensagem.pack(padx=10, pady=5, side='left')
entrada_mensagem.bind("<Return>", lambda event: enviar_mensagem())

botao_enviar = tk.Button(
    janela, 
    text="Enviar", 
    command=enviar_mensagem, 
    fg='white', 
    bg='#7289da',
    activebackground='#5b6eae',
    font=('Verdana', 10, 'bold')
)
botao_enviar.pack(padx=5, pady=5, side='left')

# Botão para abrir janela de emojis

botao_emoji = tk.Button(
    janela,
    text="😀",
    command=lambda: abrir_janela_emojis(),
    fg='white',
    bg='#7289da',
    activebackground='#5b6eae',
    font=('Verdana', 10, 'bold')
)
botao_emoji.pack(padx=5, pady=5, side='left')

# Botão para enviar arquivos

botao_arquivo = tk.Button(
    janela,
    text="📎 Arquivo",
    command=enviar_arquivo,
    fg='white',
    bg='#7289da',
    activebackground='#5b6eae',
    font=('Verdana', 10, 'bold')
)
botao_arquivo.pack(padx=5, pady=5, side='left')



# Perguntar o nome do usuário

nome = simpledialog.askstring("Nome", "Digite seu nome:")

# Conectar ao servidor

HOST = '192.168.100.81'
PORT = 12345

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

# Enviar nome ao entrar

cliente.send(f"{nome} entrou no chat.".encode('utf-8'))

# Thread para receber mensagens

thread_receber = threading.Thread(target=receber_mensagens)
thread_receber.daemon = True
thread_receber.start()

# Iniciar a interface

janela.mainloop()