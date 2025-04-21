import socket
import threading
from datetime import datetime


class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.running = True
            print(f"Servidor ouvindo em {self.host}:{self.port}")

            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")

    def accept_connections(self):
        while self.running:
            try:
                client, address = self.server_socket.accept()
                print(f"Conexão aceita de {address}")

                # Receber nome do cliente
                client_name = client.recv(1024).decode('utf-8')
                if client_name:
                    self.broadcast(f"{client_name} entrou no chat.", client)

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client, client_name)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    self.clients.append((client, client_name))
            except:
                if self.running:
                    print("Erro ao aceitar conexão")
                break

    def handle_client(self, client, client_name):
        while self.running:
            try:
                message = client.recv(1024).decode('utf-8')
                if not message:
                    break

                if message.startswith("/file:"):
                    self.handle_file(client, message, client_name)
                else:
                    timestamp = datetime.now().strftime("%H:%M")
                    formatted_msg = f"[{timestamp}] {client_name}: {message}"
                    print(f"Mensagem recebida: {formatted_msg}")
                    self.broadcast(formatted_msg, client)
            except:
                break

        # Remover cliente quando desconectar
        self.remove_client(client, client_name)

    def handle_file(self, client, message, sender_name):
        filename = message.split(":", 1)[1]
        try:
            data = client.recv(1024 * 1024)  # 1MB max
            timestamp = datetime.now().strftime("%H:%M")
            notification = f"[{timestamp}] {sender_name} enviou um arquivo: {filename}"

            print(notification)
            for c, _ in self.clients:
                if c != client:
                    try:
                        c.send(f"/file:{filename}".encode('utf-8'))
                        c.sendall(data)
                        c.send(notification.encode('utf-8'))
                    except:
                        continue
        except Exception as e:
            print(f"Erro ao processar arquivo: {e}")

    def broadcast(self, message, sender_client=None):
        for client, _ in self.clients:
            if client != sender_client:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    continue

    def remove_client(self, client, client_name):
        for i, (c, name) in enumerate(self.clients):
            if c == client:
                self.clients.pop(i)
                break
        client.close()
        self.broadcast(f"{client_name} saiu do chat.")
        print(f"{client_name} desconectou")

    def stop(self):
        self.running = False
        self.broadcast("O servidor está sendo desligado.")
        for client, _ in self.clients:
            client.close()
        self.server_socket.close()
        print("Servidor desligado")


if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
        input("Pressione Enter para parar o servidor...\n")
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()