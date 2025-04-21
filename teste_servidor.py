import socket

HOST = '0.0.0.0'
PORT = 12345

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
print("Servidor de teste aguardando conexão...")

conn, addr = s.accept()
print(f"Conexão recebida de {addr}")
conn.send(b'Conectado com sucesso!')
conn.close()
