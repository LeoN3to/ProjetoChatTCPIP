import socket
import threading
from datetime import datetime
import logging


class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        """Inicializa o servidor de chat"""
        self.host = host
        self.port = port
        self.clients = []  # Lista de clientes conectados (socket, nome)
        self.server_socket = None
        self.running = False

        # Configuração de logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ChatServer')

    def start(self):
        """Inicia o servidor"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # Permite até 5 conexões pendentes
            self.running = True

            self.logger.info(f"Servidor iniciado em {self.host}:{self.port}. Aguardando conexões...")

            # Thread para aceitar conexões
            accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
            accept_thread.start()

            # Mantém o servidor ativo
            while self.running:
                pass

        except Exception as e:
            self.logger.error(f"Erro ao iniciar servidor: {e}", exc_info=True)
            self.stop()

    def accept_connections(self):
        """Aceita novas conexões de clientes"""
        while self.running:
            try:
                client, address = self.server_socket.accept()
                self.logger.info(f"Nova conexão de {address}")

                # Thread para receber o nome do cliente
                name_thread = threading.Thread(
                    target=self.receive_client_name,
                    args=(client, address),
                    daemon=True
                )
                name_thread.start()

            except OSError as e:
                if self.running:
                    self.logger.error(f"Erro ao aceitar conexão: {e}")
                break
            except Exception as e:
                self.logger.error(f"Erro inesperado: {e}", exc_info=True)
                continue

    def receive_client_name(self, client, address):
        """Recebe e registra o nome do cliente"""
        try:
            # Recebe o nome do cliente (primeira mensagem obrigatória)
            name_data = client.recv(1024)
            if not name_data:
                raise ConnectionError("Cliente desconectou antes de enviar nome")

            client_name = name_data.decode('utf-8').strip()

            if not client_name:
                raise ValueError("Nome do cliente vazio")

            # Adiciona à lista de clientes
            self.clients.append((client, client_name))
            self.logger.info(f"Cliente registrado: {client_name} ({address})")

            # Notifica todos sobre o novo usuário
            self.broadcast(f"{client_name} entrou no chat.", exclude_client=client)

            # Inicia thread para receber mensagens deste cliente
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client, client_name),
                daemon=True
            )
            client_thread.start()

        except Exception as e:
            self.logger.error(f"Erro ao registrar cliente {address}: {e}")
            client.close()

    def handle_client(self, client, client_name):
        """Gerencia a comunicação com um cliente específico"""
        while self.running:
            try:
                message = client.recv(1024).decode('utf-8')

                if not message:  # Cliente desconectou
                    break

                if message.startswith("/file:"):
                    self.handle_file(client, message, client_name)
                else:
                    timestamp = datetime.now().strftime("%H:%M")
                    formatted_msg = f"[{timestamp}] {client_name}: {message}"
                    self.logger.info(f"Mensagem de {client_name}: {message}")
                    self.broadcast(formatted_msg, exclude_client=client)

            except ConnectionResetError:
                break
            except Exception as e:
                self.logger.error(f"Erro com cliente {client_name}: {e}")
                break

        self.remove_client(client, client_name)

    def handle_file(self, client, header, sender_name):
        """Processa o recebimento de um arquivo"""
        try:
            filename = header.split(":", 1)[1]
            file_data = client.recv(1024 * 1024)  # 1MB máximo

            timestamp = datetime.now().strftime("%H:%M")
            notification = f"[{timestamp}] {sender_name} enviou um arquivo: {filename}"
            self.logger.info(notification)

            # Envia para todos os clientes, exceto o remetente
            for c, name in self.clients:
                if c != client:
                    try:
                        c.send(f"/file:{filename}".encode('utf-8'))
                        c.sendall(file_data)
                        c.send(notification.encode('utf-8'))
                    except:
                        continue

        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo de {sender_name}: {e}")

    def broadcast(self, message, exclude_client=None):
        """Envia mensagem para todos os clientes, exceto o especificado"""
        for client, name in self.clients:
            if client != exclude_client:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    continue

    def remove_client(self, client, client_name):
        """Remove um cliente da lista e notifica os demais"""
        for i, (c, name) in enumerate(self.clients):
            if c == client:
                self.clients.pop(i)
                break

        try:
            client.close()
        except:
            pass

        leave_message = f"{client_name} saiu do chat."
        self.broadcast(leave_message)
        self.logger.info(f"Cliente desconectado: {client_name}")

    def stop(self):
        """Encerra o servidor corretamente"""
        self.running = False
        self.logger.info("Encerrando servidor...")

        # Notifica todos os clientes
        self.broadcast("O servidor está sendo desligado.")

        # Fecha todas as conexões
        for client, name in self.clients:
            try:
                client.close()
            except:
                continue

        # Fecha o socket do servidor
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        self.logger.info("Servidor encerrado com sucesso.")


if __name__ == "__main__":
    server = ChatServer()

    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()