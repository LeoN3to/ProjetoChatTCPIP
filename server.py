import socket
import threading
from datetime import datetime
import logging


class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False

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
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            self.logger.info(f"Servidor iniciado em {self.host}:{self.port}")

            # Thread principal para aceitar conexões
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

            # Mantém o servidor ativo
            while self.running:
                pass

        except Exception as e:
            self.logger.error(f"Erro ao iniciar servidor: {e}")
            self.stop()

    def accept_connections(self):
        while self.running:
            try:
                client, address = self.server_socket.accept()
                client.settimeout(180)  # Timeout de 180 segundos para estabelecer conexão
                self.logger.info(f"Conexão estabelecida com {address}")

                # Thread para lidar com o cliente
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, address)
                )
                client_thread.daemon = True
                client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erro ao aceitar conexão: {e}")

    def handle_client(self, client, address):
        try:
            # Recebe o nome do cliente com timeout
            client.settimeout(70)  # 70 segundos para enviar o nome
            name = client.recv(1024).decode('utf-8').strip()

            if not name:
                raise ValueError("Nome vazio recebido")

            self.clients.append((client, name))
            self.broadcast(f"{name} entrou no chat.", exclude=client)
            self.logger.info(f"{name} conectado de {address}")

            # Reduz timeout após conexão estabelecida
            client.settimeout(300)  # 5 minutos de inatividade

            while self.running:
                try:
                    message = client.recv(1024).decode('utf-8')
                    if not message:
                        break

                    if message.startswith("/file:"):
                        self.handle_file(client, name, message)
                    else:
                        self.broadcast(f"[{datetime.now().strftime('%H:%M')}] {name}: {message}")

                except socket.timeout:
                    continue
                except:
                    break

        except socket.timeout:
            self.logger.warning(f"Timeout na conexão com {address}")
        except Exception as e:
            self.logger.error(f"Erro com cliente {address}: {e}")
        finally:
            self.remove_client(client, name)


if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()