"""
CLIENTE DE CHAT COM INTERFACE GRÁFICA
Disciplina: Redes de Computadores
Autor: [Seu Nome]
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk, filedialog, messagebox
from tkinter.font import Font
import os
from PIL import Image, ImageTk  # Para possível implementação de ícones personalizados


class ChatApp:
    def __init__(self, root):
        """Inicializa a aplicação de chat"""
        self.root = root
        self.configure_main_window()
        self.setup_variables()
        self.setup_ui()
        self.connect_to_server()

    def configure_main_window(self):
        """Configura a janela principal"""
        self.root.title("NetLink Chat")
        self.root.geometry("800x600")
        self.root.configure(bg='#36393f')  # Cor de fundo estilo Discord
        self.root.minsize(600, 400)  # Tamanho mínimo da janela

        # Tentativa de carregar ícone (opcional)
        try:
            self.root.iconbitmap('chat_icon.ico')
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")

    def setup_variables(self):
        """Configura variáveis e estilos"""
        # Fontes
        self.main_font = Font(family="Segoe UI", size=12)
        self.title_font = Font(family="Segoe UI", size=14, weight="bold")

        # Esquema de cores
        self.bg_color = "#36393f"  # Cor principal de fundo
        self.text_bg = "#2f3136"  # Cor do fundo do chat
        self.text_fg = "#dcddde"  # Cor do texto
        self.button_bg = "#5865f2"  # Cor dos botões
        self.button_active = "#4752c4"  # Cor quando botão pressionado
        self.entry_bg = "#40444b"  # Cor do campo de entrada

        # Variáveis de conexão
        self.server_ip = '192.168.100.81'  # IP do servidor
        self.server_port = 12345  # Porta do servidor
        self.username = None  # Será definido na conexão
        self.client_socket = None  # Socket de conexão

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Área de chat (rolável)
        self.setup_chat_area(main_frame)

        # Frame de entrada (mensagens + botões)
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X)

        # Botões e campo de entrada
        self.setup_input_controls(input_frame)

    def setup_chat_area(self, parent_frame):
        """Configura a área de exibição das mensagens"""
        self.chat_area = scrolledtext.ScrolledText(
            parent_frame,
            state='disabled',  # Impede edição direta pelo usuário
            fg=self.text_fg,
            bg=self.text_bg,
            font=self.main_font,
            wrap=tk.WORD,  # Quebra de linha por palavras
            padx=10,
            pady=10
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    def setup_input_controls(self, parent_frame):
        """Configura os controles de entrada"""
        # Botão de emoji
        emoji_btn = tk.Button(
            parent_frame,
            text="😊",
            command=self.open_emoji_window,
            bg=self.button_bg,
            fg="white",
            activebackground=self.button_active,
            font=self.main_font,
            relief=tk.FLAT,
            width=3
        )
        emoji_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Botão de envio de arquivo
        file_btn = tk.Button(
            parent_frame,
            text="📎",
            command=self.send_file,
            bg=self.button_bg,
            fg="white",
            activebackground=self.button_active,
            font=self.main_font,
            relief=tk.FLAT,
            width=3
        )
        file_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Campo de entrada de mensagem
        self.message_entry = tk.Entry(
            parent_frame,
            width=50,
            fg=self.text_fg,
            bg=self.entry_bg,
            insertbackground='white',  # Cor do cursor
            font=self.main_font,
            relief=tk.FLAT
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())  # Envia com Enter

        # Botão de enviar mensagem
        send_btn = tk.Button(
            parent_frame,
            text="Enviar",
            command=self.send_message,
            bg=self.button_bg,
            fg="white",
            activebackground=self.button_active,
            font=self.main_font,
            relief=tk.FLAT
        )
        send_btn.pack(side=tk.LEFT)

    def connect_to_server(self):
        """Estabelece conexão com o servidor"""
        # Solicita nome de usuário
        self.username = simpledialog.askstring(
            "NetLink Chat",
            "Digite seu nome:",
            parent=self.root
        )

        # Validação do nome
        if not self.username:
            messagebox.showerror("Erro", "Você precisa digitar um nome para entrar no chat.")
            self.root.destroy()
            return

        try:
            # Cria socket TCP/IP
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Tenta conexão com o servidor
            self.client_socket.connect((self.server_ip, self.server_port))

            # Envia mensagem de entrada no chat
            self.client_socket.send(f"{self.username} entrou no chat.".encode('utf-8'))

            # Inicia thread para receber mensagens
            self.receive_thread = threading.Thread(
                target=self.receive_messages,
                daemon=True  # Thread encerra quando o programa principal encerrar
            )
            self.receive_thread.start()

        except Exception as e:
            messagebox.showerror(
                "Erro de Conexão",
                f"Não foi possível conectar ao servidor em {self.server_ip}:{self.server_port}\n"
                f"Erro: {str(e)}"
            )
            self.root.destroy()

    def receive_messages(self):
        """Fica ouvindo mensagens do servidor"""
        while True:
            try:
                # Recebe mensagem (bloqueante)
                message = self.client_socket.recv(1024).decode('utf-8')

                if not message:  # Conexão foi fechada
                    break

                # Verifica se é um arquivo
                if message.startswith("/file:"):
                    self.handle_file_reception(message)
                else:
                    # Mensagem de texto normal
                    self.show_message(message)

            except ConnectionResetError:
                self.show_message("Conexão com o servidor foi perdida.")
                break
            except Exception as e:
                self.show_message(f"Erro ao receber mensagem: {str(e)}")
                break

        # Fecha a conexão se sair do loop
        self.client_socket.close()

    def handle_file_reception(self, header):
        """Processa recebimento de arquivo"""
        try:
            # Extrai nome do arquivo do cabeçalho
            filename = header.split(":", 1)[1]

            # Recebe dados do arquivo (1MB máximo)
            file_data = self.client_socket.recv(1024 * 1024)

            # Diálogo para salvar o arquivo
            save_path = filedialog.asksaveasfilename(
                initialfile=f"recebido_{filename}",
                title="Salvar arquivo recebido",
                filetypes=[("Todos os arquivos", "*.*")]
            )

            if save_path:  # Se usuário selecionou local
                with open(save_path, "wb") as file:
                    file.write(file_data)
                self.show_message(f"Arquivo recebido e salvo como: {save_path}")

        except Exception as e:
            self.show_message(f"Erro ao receber arquivo: {str(e)}")

    def show_message(self, message):
        """Exibe mensagem na área de chat"""
        self.chat_area.config(state='normal')  # Habilita edição temporária
        self.chat_area.insert('end', message + '\n')
        self.chat_area.config(state='disabled')  # Desabilita edição
        self.chat_area.see('end')  # Rola para a última mensagem

    def send_message(self):
        """Envia mensagem para o servidor"""
        message = self.message_entry.get().strip()
        self.message_entry.delete(0, 'end')  # Limpa campo

        if message:  # Só envia se não estiver vazio
            # Formata mensagem com nome de usuário
            formatted_message = f"{self.username}: {message}"

            # Exibe localmente
            self.show_message(formatted_message)

            try:
                # Envia para servidor
                self.client_socket.send(formatted_message.encode('utf-8'))
            except Exception as e:
                self.show_message(f"Erro ao enviar mensagem: {str(e)}")

    def send_file(self):
        """Envia arquivo para o servidor"""
        # Diálogo para selecionar arquivo
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo para enviar"
        )

        if not filepath:  # Usuário cancelou
            return

        try:
            # Lê arquivo em modo binário
            with open(filepath, 'rb') as file:
                file_data = file.read()

            # Obtém apenas o nome do arquivo (sem caminho)
            filename = os.path.basename(filepath)

            # Envia cabeçalho com nome do arquivo
            self.client_socket.send(f"/file:{filename}".encode('utf-8'))

            # Envia dados do arquivo
            self.client_socket.sendall(file_data)

            # Feedback para usuário
            self.show_message(f"Você enviou o arquivo '{filename}'")

        except Exception as e:
            self.show_message(f"Erro ao enviar arquivo: {str(e)}")

    def open_emoji_window(self):
        """Abre janela de seleção de emojis"""
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("Selecionar Emoji")
        emoji_window.configure(bg=self.bg_color)
        emoji_window.resizable(False, False)

        # Cria abas para categorias
        notebook = ttk.Notebook(emoji_window)
        notebook.pack(padx=10, pady=10)

        # Dicionário de emojis por categoria
        emoji_categories = {
            "Carinhas": ['😀', '😂', '😍', '😢', '😡', '😎', '🤩', '🥳', '😴', '🤯'],
            "Gestos": ['👍', '🙏', '👎', '🤙', '👏', '👌', '🤝', '✌️', '🤘', '🤞'],
            "Símbolos": ['❤️', '💔', '🎉', '💀', '✨', '🔥', '🌟', '💎', '⚡', '🌈']
        }

        # Cria uma aba para cada categoria
        for category_name, emojis in emoji_categories.items():
            frame = tk.Frame(notebook, bg=self.bg_color)
            notebook.add(frame, text=category_name)

            # Adiciona botões para cada emoji
            for i, emoji in enumerate(emojis):
                btn = tk.Button(
                    frame,
                    text=emoji,
                    font=("Arial", 14),
                    command=lambda e=emoji: self.insert_emoji(e, emoji_window),
                    bg=self.button_bg,
                    fg="white",
                    activebackground=self.button_active,
                    relief=tk.FLAT
                )
                # Organiza em grid 5 colunas
                btn.grid(row=i // 5, column=i % 5, padx=5, pady=5)

    def insert_emoji(self, emoji, window):
        """Insere emoji no campo de mensagem e fecha janela"""
        self.message_entry.insert(tk.END, emoji)
        window.destroy()


if __name__ == "__main__":
    # Cria e inicia aplicação
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()