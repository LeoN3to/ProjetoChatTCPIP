
import socket
import threading

thread_receber = threading.Thread(target=receber_mensagens)
thread_receber.start()
# Configurações do cliente
HOST = '127.0.0.1'
PORT = 12345

# Criar socket do cliente
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

# Função para receber mensagens do servidor
def receber_mensagens():
    while True:
        try:
            mensagem = cliente.recv(1024).decode('utf-8')
            print(f"\nNova mensagem: {mensagem}")
        except:
            print("Erro ao receber mensagem ou conexão encerrada.")
            cliente.close()
            break
        # Thread para receber mensagens

# Enviar mensagens
print("Digite suas mensagens:")
while True:
    mensagem = input()
    cliente.send(mensagem.encode('utf-8'))