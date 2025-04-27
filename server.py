import socket
import threading

# Lista para armazenar conexões de clientes
clientes = []

# Configurações do servidor
host = '0.0.0.0'
porta = 12345

# Função para enviar mensagem para todos os clientes conectados
def broadcast(mensagem, origem=None):
    for cliente in clientes:
        if cliente != origem:
            try:
                cliente.sendall(mensagem)
            except:
                clientes.remove(cliente)

# Função principal que lida com cada cliente
def lidar_com_cliente(cliente_socket, endereco):
    try:
        nome_usuario = cliente_socket.recv(1024).decode('utf-8')
        print(f"{nome_usuario} ({endereco}) entrou no chat.")
        broadcast(f"{nome_usuario} entrou no chat.".encode('utf-8'))

        while True:
            try:
                dados = cliente_socket.recv(4096)

                if not dados:
                    break

                # Detecta início de envio de arquivo
                if dados.startswith(b'!@#ARQUIVO_INICIO#@!'):
                    buffer = b""
                    while True:
                        parte = cliente_socket.recv(4096)
                        if b'!@#ARQUIVO_FIM#@!' in parte:
                            # Última parte do arquivo
                            fim_arquivo = parte.split(b'!@#ARQUIVO_FIM#@!')[0]
                            buffer += fim_arquivo
                            break
                        else:
                            buffer += parte

                    # Agora "buffer" tem o arquivo inteiro
                    broadcast(b'!@#ARQUIVO_INICIO#@!', origem=cliente_socket)
                    broadcast(buffer, origem=cliente_socket)
                    broadcast(b'!@#ARQUIVO_FIM#@!', origem=cliente_socket)

                else:
                    # Mensagem normal de texto
                    broadcast(dados, origem=cliente_socket)

            except Exception as e:
                print(f"Erro ao receber dados de {endereco}: {e}")
                break

    finally:
        # Cliente saiu
        if cliente_socket in clientes:
            clientes.remove(cliente_socket)
        cliente_socket.close()
        print(f"{nome_usuario} ({endereco}) saiu do chat.")
        broadcast(f"{nome_usuario} saiu do chat.".encode('utf-8'))

# Inicia o servidor
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, porta))
    servidor.listen(5)

    print(f"Servidor rodando em {host}:{porta}")

    while True:
        cliente_socket, endereco = servidor.accept()
        clientes.append(cliente_socket)

        # Inicia uma thread para cada cliente
        thread = threading.Thread(target=lidar_com_cliente, args=(cliente_socket, endereco))
        thread.start()

if __name__ == "__main__":
    iniciar_servidor()
