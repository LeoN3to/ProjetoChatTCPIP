import socket
import threading

# Configurações do servidor

HOST = '0.0.0.0'  # localhost
PORT = 12345

# Lista que armazena os clientes conectados

clientes = []

# Função para processar cada cliente

def lidar_com_cliente(cliente):
    while True:
        try:
            mensagem = cliente.recv(1024).decode('utf-8')
            if mensagem.startswith("/file:"):
                nome_arquivo = mensagem.split(":", 1)[1]
                dados = cliente.recv(1024 * 1024)
                for c in clientes:
                    if c != cliente:
                        c.send(f"/file:{nome_arquivo}".encode('utf-8'))
                        c.sendall(dados)
            elif mensagem:
                print(f"Mensagem recebida: {mensagem}")
                for c in clientes:
                    if c != cliente:
                        c.send(mensagem.encode('utf-8'))
        except:
            if cliente in clientes:
                clientes.remove(cliente)
            cliente.close()
            break


# Criar socket do servidor

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORT))
servidor.listen()

print(f"Servidor ouvindo em {HOST}:{PORT}")

# Aceitar conexões de clientes

while True:
    cliente, endereco = servidor.accept()
    print(f"Conexão aceita de {endereco}")
    clientes.append(cliente)

    # Criar uma thread para lidar com o cliente

    thread = threading.Thread(target=lidar_com_cliente, args=(cliente,))
    thread.start()