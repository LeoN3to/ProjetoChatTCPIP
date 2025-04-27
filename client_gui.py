import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk, filedialog, messagebox
from tkinter.font import Font
import os
from datetime import datetime

class ChatApp:
    def __init__(self, root):
        # Inicializa o chat
        self.root = root
        self.configurar_janela()
        self.criar_variaveis()
        self.montar_interface()
        self.conectar_no_servidor()

    def configurar_janela(self):
        self.root.title("NetLink Chat")
        self.root.geometry("800x600")
        self.root.configure(bg='#36393f')
        self.root.minsize(600, 400)
        try:
            self.root.iconbitmap('chat_icon.ico')
        except:
            pass

    def criar_variaveis(self):
        self.fonte_principal = Font(family="Segoe UI", size=12)
        self.fonte_titulo = Font(family="Segoe UI", size=14, weight="bold")

        self.cor_fundo = "#36393f"
        self.cor_texto_fundo = "#2f3136"
        self.cor_texto = "#dcddde"
        self.cor_botao = "#5865f2"
        self.cor_botao_ativo = "#4752c4"
        self.cor_campo = "#40444b"

        self.porta_servidor = 12345
        self.nome_usuario = None
        self.socket_cliente = None
        self.thread_receber = None
        self.conexao_ativa = False

    def montar_interface(self):
        frame_principal = tk.Frame(self.root, bg=self.cor_fundo)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.area_chat = scrolledtext.ScrolledText(
            frame_principal,
            state='disabled',
            fg=self.cor_texto,
            bg=self.cor_texto_fundo,
            font=self.fonte_principal,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.area_chat.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        frame_entrada = tk.Frame(frame_principal, bg=self.cor_fundo)
        frame_entrada.pack(fill=tk.X)

        botao_emoji = tk.Button(
            frame_entrada,
            text="😊",
            command=self.abrir_janela_emojis,
            bg=self.cor_botao,
            fg="white",
            activebackground=self.cor_botao_ativo,
            font=self.fonte_principal,
            relief=tk.FLAT,
            width=3
        )
        botao_emoji.pack(side=tk.LEFT, padx=(0, 5))

        botao_arquivo = tk.Button(
            frame_entrada,
            text="📎",
            command=self.enviar_arquivo,
            bg=self.cor_botao,
            fg="white",
            activebackground=self.cor_botao_ativo,
            font=self.fonte_principal,
            relief=tk.FLAT,
            width=3
        )
        botao_arquivo.pack(side=tk.LEFT, padx=(0, 5))

        self.campo_mensagem = tk.Entry(
            frame_entrada,
            width=50,
            fg=self.cor_texto,
            bg=self.cor_campo,
            insertbackground='white',
            font=self.fonte_principal,
            relief=tk.FLAT
        )
        self.campo_mensagem.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.campo_mensagem.bind("<Return>", lambda e: self.enviar_mensagem())

        botao_enviar = tk.Button(
            frame_entrada,
            text="Enviar",
            command=self.enviar_mensagem,
            bg=self.cor_botao,
            fg="white",
            activebackground=self.cor_botao_ativo,
            font=self.fonte_principal,
            relief=tk.FLAT
        )
        botao_enviar.pack(side=tk.LEFT)

        self.botao_conexao = tk.Button(
            frame_principal,
            text="Reconectar",
            command=self.tentar_reconectar,
            bg="#7289da",
            fg="white",
            font=self.fonte_principal,
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.botao_conexao.pack(pady=5)

        self.botao_reconectar = tk.Button(self.root, text="Reconectar", command=self.tentar_reconectar)
        self.botao_reconectar.pack(pady=5)
        self.botao_reconectar.config(state=tk.DISABLED)

    def ta_conectado(self):
        return (self.conexao_ativa and self.socket_cliente and
                hasattr(self.socket_cliente, 'fileno') and self.socket_cliente.fileno() != -1)

    def conectar_no_servidor(self):
        self.fechar_conexao()
        ip_servidor = simpledialog.askstring(
            "Configuração de Conexão",
            "Digite o IP do servidor:",
            parent=self.root,
            initialvalue="127.0.0.1"
        )

        if not ip_servidor:
            messagebox.showerror("Erro", "Você deve informar o IP do servidor.")
            return

        self.nome_usuario = simpledialog.askstring(
            "NetLink Chat",
            "Digite seu nome:",
            parent=self.root
        )

        if not self.nome_usuario:
            messagebox.showerror("Erro", "Você precisa digitar um nome para entrar no chat.")
            return

        try:
            self.mostrar_mensagem("Conectando ao servidor...")

            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.settimeout(30)
            self.socket_cliente.connect((ip_servidor, self.porta_servidor))
            self.socket_cliente.settimeout(None)
            self.conexao_ativa = True

            self.socket_cliente.send(self.nome_usuario.encode('utf-8'))

            mensagem_boas_vindas = f"Conectado como {self.nome_usuario}"
            self.mostrar_mensagem(mensagem_boas_vindas)

            self.thread_receber = threading.Thread(target=self.pegar_mensagens, daemon=True)
            self.thread_receber.start()

            self.botao_conexao.config(state=tk.DISABLED)

        except socket.timeout:
            self.mostrar_mensagem("Erro: Tempo esgotado ao conectar ao servidor")
            self.botao_conexao.config(state=tk.NORMAL)
        except Exception as e:
            self.mostrar_mensagem(f"Erro de conexão: {str(e)}")
            self.botao_conexao.config(state=tk.NORMAL)

    def tentar_reconectar(self):
        self.conectar_no_servidor()
        self.botao_reconectar.config(state=tk.DISABLED)

    def fechar_conexao(self):
        if hasattr(self, 'socket_cliente') and self.socket_cliente:
            try:
                self.socket_cliente.close()
            except:
                pass
        self.conexao_ativa = False
        self.socket_cliente = None

    def pegar_mensagens(self):
        while self.ta_conectado():
            try:
                dados = self.socket_cliente.recv(4096)

                if not dados:
                    self.root.after(0, self.mostrar_mensagem, "Servidor desconectou")
                    break

                if dados.startswith(b'/file:'):
                    partes = dados.split(b':', 2)
                    if len(partes) == 3:
                        nome_arquivo = partes[1].decode('utf-8')
                        dados_arquivo = partes[2]

                        caminho_salvar = filedialog.asksaveasfilename(
                            initialfile=f"recebido_{nome_arquivo}",
                            title="Salvar arquivo recebido"
                        )

                        if caminho_salvar:
                            with open(caminho_salvar, "wb") as f:
                                f.write(dados_arquivo)
                            self.mostrar_mensagem(f"Arquivo recebido: {nome_arquivo}")
                        else:
                            self.mostrar_mensagem(f"Recebeu arquivo {nome_arquivo} (não salvo)")
                    else:
                        self.mostrar_mensagem("Formato de arquivo recebido inválido.")

                else:
                    try:
                        mensagem = dados.decode('utf-8')
                        if not mensagem.startswith(f"{self.nome_usuario}:"):
                            hora_atual = datetime.now().strftime('%H:%M')
                            mensagem_formatada = f"[{hora_atual}] {mensagem}"
                            self.root.after(0, self.mostrar_mensagem, mensagem_formatada)
                    except UnicodeDecodeError:
                        self.mostrar_mensagem("Mensagem inválida recebida")

            except Exception as e:
                self.root.after(0, self.mostrar_mensagem, f"Erro na conexão: {str(e)}")
                break

        self.root.after(0, self.perdeu_conexao)

    def perdeu_conexao(self):
        self.fechar_conexao()
        self.botao_conexao.config(state=tk.NORMAL)
        self.mostrar_mensagem("Desconectado. Clique em 'Reconectar' para tentar novamente.")
        self.botao_reconectar.config(state=tk.NORMAL)

    def mostrar_mensagem(self, mensagem):
        self.area_chat.config(state='normal')
        self.area_chat.insert('end', mensagem + '\n')
        self.area_chat.config(state='disabled')
        self.area_chat.see('end')

    def enviar_mensagem(self):
        if not self.ta_conectado():
            self.mostrar_mensagem("Erro: Não conectado ao servidor")
            return

        mensagem = self.campo_mensagem.get().strip()
        self.campo_mensagem.delete(0, 'end')

        if mensagem:
            hora_atual = datetime.now().strftime('%H:%M')
            mensagem_para_servidor = f"{self.nome_usuario}: {mensagem}"
            mensagem_local = f"[{hora_atual}] {self.nome_usuario}: {mensagem}"

            self.mostrar_mensagem(mensagem_local)

            try:
                self.socket_cliente.send(mensagem_para_servidor.encode('utf-8'))
            except socket.timeout:
                self.mostrar_mensagem("Erro: Tempo esgotado ao enviar mensagem")
            except Exception as e:
                self.mostrar_mensagem(f"Erro ao enviar mensagem: {str(e)}")
                self.perdeu_conexao()

    def enviar_arquivo(self):
        if not self.ta_conectado():
            self.mostrar_mensagem("Erro: Não conectado ao servidor")
            return

        caminho_arquivo = filedialog.askopenfilename(
            title="Selecionar arquivo para enviar"
        )

        if not caminho_arquivo:
            return

        try:
            with open(caminho_arquivo, 'rb') as arquivo:
                dados_arquivo = arquivo.read()

            nome_arquivo = os.path.basename(caminho_arquivo)

            if len(dados_arquivo) > 10 * 1024 * 1024:  # Limite 10MB
                self.mostrar_mensagem("Erro: Arquivo muito grande (limite 10MB)")
                return

            conteudo = b"/file:" + nome_arquivo.encode('utf-8') + b":" + dados_arquivo
            self.socket_cliente.sendall(conteudo)

            self.mostrar_mensagem(f"Você enviou: {nome_arquivo}")

        except socket.timeout:
            self.mostrar_mensagem("Erro: Tempo esgotado ao enviar arquivo")
        except Exception as e:
            self.mostrar_mensagem(f"Erro ao enviar arquivo: {str(e)}")
            self.perdeu_conexao()

    def abrir_janela_emojis(self):
        janela_emoji = tk.Toplevel(self.root)
        janela_emoji.title("Selecionar Emoji")
        janela_emoji.configure(bg=self.cor_fundo)
        janela_emoji.resizable(False, False)

        abas = ttk.Notebook(janela_emoji)
        abas.pack(padx=10, pady=10)

        categorias_emojis = {
            "Carinhas": ['😀', '😂', '😍', '😢', '😡', '😎', '🤩', '🥳', '😴', '🤯'],
            "Gestos": ['👍', '🙏', '👎', '🤙', '👏', '👌', '🤝', '✌️', '🤘', '🤞'],
            "Símbolos": ['❤️', '💔', '🎉', '💀', '✨', '🔥', '🌟', '💎', '⚡', '🌈']
        }

        for nome_categoria, emojis in categorias_emojis.items():
            frame = tk.Frame(abas, bg=self.cor_fundo)
            abas.add(frame, text=nome_categoria)

            for i, emoji in enumerate(emojis):
                botao = tk.Button(
                    frame,
                    text=emoji,
                    font=("Arial", 14),
                    command=lambda e=emoji: self.inserir_emoji(e, janela_emoji),
                    bg=self.cor_botao,
                    fg="white",
                    activebackground=self.cor_botao_ativo,
                    relief=tk.FLAT
                )
                botao.grid(row=i // 5, column=i % 5, padx=5, pady=5)

    def inserir_emoji(self, emoji, janela):
        self.campo_mensagem.insert(tk.END, emoji)
        janela.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
