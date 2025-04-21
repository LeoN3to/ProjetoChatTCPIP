import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk, filedialog, messagebox
from tkinter.font import Font
import os
from PIL import Image, ImageTk


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NetLink Chat")
        self.root.geometry("800x600")
        self.root.configure(bg='#36393f')
        self.root.minsize(600, 400)

        # Configurar ícone
        try:
            self.root.iconbitmap('chat_icon.ico')  # Adicione um arquivo .ico na pasta
        except:
            pass

        # Fontes personalizadas
        self.main_font = Font(family="Segoe UI", size=12)
        self.title_font = Font(family="Segoe UI", size=14, weight="bold")

        # Cores
        self.bg_color = "#36393f"
        self.text_bg = "#2f3136"
        self.text_fg = "#dcddde"
        self.button_bg = "#5865f2"
        self.button_active = "#4752c4"
        self.entry_bg = "#40444b"

        self.setup_ui()
        self.connect_to_server()

    def setup_ui(self):
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
        self.username = simpledialog.askstring("NetLink Chat", "Digite seu nome:", parent=self.root)
        if not self.username:
            messagebox.showerror("Erro", "Você precisa digitar um nome para entrar no chat.")
            self.root.destroy()
            return

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(('192.168.100.81', 12345))
            self.client.send(f"{self.username} entrou no chat.".encode('utf-8'))

            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor:\n{str(e)}")
            self.root.destroy()

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message.startswith("/file:"):
                    filename = message.split(":", 1)[1]
                    data = self.client.recv(1024 * 1024)
                    save_path = filedialog.asksaveasfilename(
                        initialfile=f"recebido_{filename}",
                        title="Salvar arquivo recebido"
                    )
                    if save_path:
                        with open(save_path, "wb") as f:
                            f.write(data)
                        self.show_message(f"Arquivo recebido e salvo como: {save_path}")
                else:
                    self.show_message(message)
            except Exception as e:
                self.show_message("Conexão encerrada.")
                self.client.close()
                break

    def show_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert('end', message + '\n')
        self.chat_area.config(state='disabled')
        self.chat_area.see('end')

    def send_message(self):
        message = self.message_entry.get()
        self.message_entry.delete(0, 'end')
        if message:
            formatted_message = f"{self.username}: {message}"
            self.show_message(formatted_message)
            self.client.send(formatted_message.encode('utf-8'))

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
                filename = os.path.basename(filepath)
                self.client.send(f"/file:{filename}".encode('utf-8'))
                self.client.sendall(data)
                self.show_message(f"Você enviou o arquivo '{filename}'")
            except Exception as e:
                self.show_message(f"Erro ao enviar arquivo: {e}")

    def open_emoji_window(self):
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("Selecionar Emoji")
        emoji_window.configure(bg=self.bg_color)
        emoji_window.resizable(False, False)

        notebook = ttk.Notebook(emoji_window)
        notebook.pack(padx=10, pady=10)

        categories = {
            "Carinhas": ['😀', '😂', '😍', '😢', '😡', '😎', '🤩', '🥳', '😴', '🤯'],
            "Gestos": ['👍', '🙏', '👎', '🤙', '👏', '👌', '🤝', '✌️', '🤘', '🤞'],
            "Símbolos": ['❤️', '💔', '🎉', '💀', '✨', '🔥', '🌟', '💎', '⚡', '🌈']
        }

        for category_name, emoji_list in categories.items():
            frame = tk.Frame(notebook, bg=self.bg_color)
            notebook.add(frame, text=category_name)

            for i, emoji in enumerate(emoji_list):
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
        self.message_entry.insert(tk.END, emoji)
        window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()