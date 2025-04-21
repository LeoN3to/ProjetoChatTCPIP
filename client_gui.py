import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk, filedialog, messagebox
from tkinter.font import Font
import os


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
        self.root.configure(bg='#36393f')
        self.root.minsize(600, 400)

        try:
            self.root.iconbitmap('chat_icon.ico')
        except:
            pass

    def setup_variables(self):
        """Configura variáveis e estilos"""
        # Fontes
        self.main_font = Font(family="Segoe UI", size=12)
        self.title_font = Font(family="Segoe UI", size=14, weight="bold")

        # Esquema de cores
        self.bg_color = "#36393f"
        self.text_bg = "#2f3136"
        self.text_fg = "#dcddde"
        self.button_bg = "#5865f2"
        self.button_active = "#4752c4"
        self.entry_bg = "#40444b"

        # Variáveis de conexão
        self.server_port = 12345
        self.username = None
        self.client_socket = None
        self.receive_thread = None

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Área de chat
        self.chat_area = scrolledtext.ScrolledText(
            main_frame,
            state='disabled',
            fg=self.text_fg,
            bg=self.text_bg,
            font=self.main_font,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Frame de entrada
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X)

        # Botão de emoji
        emoji_btn = tk.Button(
            input_frame,
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

        # Botão de arquivo
        file_btn = tk.Button(
            input_frame,
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
            input_frame,
            width=50,
            fg=self.text_fg,
            bg=self.entry_bg,
            insertbackground='white',
            font=self.main_font,
            relief=tk.FLAT
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        # Botão de enviar
        send_btn = tk.Button(
            input_frame,
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
        """Estabelece conexão com o servidor usando socket e threading"""
        # Primeiro pede o IP do servidor
        server_ip = simpledialog.askstring(
            "Configuração de Conexão",
            "Digite o IP do servidor:",
            parent=self.root,
            initialvalue="127.0.0.1"  # Default para localhost
        )

        if not server_ip:
            messagebox.showerror("Erro", "Você deve informar o IP do servidor.")
            self.root.destroy()
            return

        # Depois pede o nome de usuário
        self.username = simpledialog.askstring(
            "NetLink Chat",
            "Digite seu nome:",
            parent=self.root
        )

        if not self.username:
            messagebox.showerror("Erro", "Você precisa digitar um nome para entrar no chat.")
            self.root.destroy()
            return

        try:
            # Cria socket TCP/IP
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)  # Timeout de 5 segundos

            # Tenta conexão com o servidor
            self.client_socket.connect((server_ip, self.server_port))

            # Primeiro envia apenas o nome de usuário (requerido pelo servidor)
            self.client_socket.send(self.username.encode('utf-8'))

            # Depois envia mensagem de entrada
            entry_message = f"{self.username} entrou no chat."
            self.client_socket.send(entry_message.encode('utf-8'))
            self.show_message(entry_message)

            # Inicia thread para receber mensagens
            self.receive_thread = threading.Thread(
                target=self.receive_messages,
                daemon=True
            )
            self.receive_thread.start()

        except socket.timeout:
            messagebox.showerror(
                "Erro de Conexão",
                f"Tempo excedido ao tentar conectar ao servidor {server_ip}:{self.server_port}"
            )
            self.root.destroy()
        except Exception as e:
            messagebox.showerror(
                "Erro de Conexão",
                f"Não foi possível conectar ao servidor:\n{str(e)}"
            )
            self.root.destroy()

    def receive_messages(self):
        """Thread para receber mensagens do servidor"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')

                if not message:  # Conexão foi fechada
                    break

                if message.startswith("/file:"):
                    self.handle_file_reception(message)
                else:
                    # Atualiza a interface gráfica na thread principal
                    self.root.after(0, self.show_message, message)

            except ConnectionResetError:
                self.root.after(0, self.show_message, "Conexão com o servidor foi perdida.")
                break
            except Exception as e:
                self.root.after(0, self.show_message, f"Erro ao receber mensagem: {str(e)}")
                break

        self.client_socket.close()

    def handle_file_reception(self, header):
        """Processa recebimento de arquivo"""
        try:
            filename = header.split(":", 1)[1]
            file_data = self.client_socket.recv(1024 * 1024)  # 1MB máximo

            # Usa after para executar na thread principal
            self.root.after(0, self.process_received_file, filename, file_data)

        except Exception as e:
            self.root.after(0, self.show_message, f"Erro ao receber arquivo: {str(e)}")

    def process_received_file(self, filename, file_data):
        """Processa o arquivo recebido (executado na thread principal)"""
        save_path = filedialog.asksaveasfilename(
            initialfile=f"recebido_{filename}",
            title="Salvar arquivo recebido",
            filetypes=[("Todos os arquivos", "*.*")]
        )

        if save_path:
            try:
                with open(save_path, "wb") as file:
                    file.write(file_data)
                self.show_message(f"Arquivo recebido e salvo como: {save_path}")
            except Exception as e:
                self.show_message(f"Erro ao salvar arquivo: {str(e)}")

    def show_message(self, message):
        """Exibe mensagem na área de chat"""
        self.chat_area.config(state='normal')
        self.chat_area.insert('end', message + '\n')
        self.chat_area.config(state='disabled')
        self.chat_area.see('end')

    def send_message(self):
        """Envia mensagem para o servidor"""
        message = self.message_entry.get().strip()
        self.message_entry.delete(0, 'end')

        if message:
            formatted_message = f"{self.username}: {message}"
            self.show_message(formatted_message)

            try:
                self.client_socket.send(formatted_message.encode('utf-8'))
            except Exception as e:
                self.show_message(f"Erro ao enviar mensagem: {str(e)}")

    def send_file(self):
        """Envia arquivo para o servidor"""
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo para enviar"
        )

        if not filepath:
            return

        try:
            with open(filepath, 'rb') as file:
                file_data = file.read()

            filename = os.path.basename(filepath)

            # Envia cabeçalho do arquivo
            self.client_socket.send(f"/file:{filename}".encode('utf-8'))
            # Envia dados do arquivo
            self.client_socket.sendall(file_data)

            self.show_message(f"Você enviou o arquivo '{filename}'")

        except Exception as e:
            self.show_message(f"Erro ao enviar arquivo: {str(e)}")

    def open_emoji_window(self):
        """Abre janela de seleção de emojis"""
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("Selecionar Emoji")
        emoji_window.configure(bg=self.bg_color)
        emoji_window.resizable(False, False)

        notebook = ttk.Notebook(emoji_window)
        notebook.pack(padx=10, pady=10)

        emoji_categories = {
            "Carinhas": ['😀', '😂', '😍', '😢', '😡', '😎', '🤩', '🥳', '😴', '🤯'],
            "Gestos": ['👍', '🙏', '👎', '🤙', '👏', '👌', '🤝', '✌️', '🤘', '🤞'],
            "Símbolos": ['❤️', '💔', '🎉', '💀', '✨', '🔥', '🌟', '💎', '⚡', '🌈']
        }

        for category_name, emojis in emoji_categories.items():
            frame = tk.Frame(notebook, bg=self.bg_color)
            notebook.add(frame, text=category_name)

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
                btn.grid(row=i // 5, column=i % 5, padx=5, pady=5)

    def insert_emoji(self, emoji, window):
        """Insere emoji no campo de mensagem e fecha janela"""
        self.message_entry.insert(tk.END, emoji)
        window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()