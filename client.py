import socket

TCP_IP = '192.168.0.103'
TCP_PORT = 8030
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

while True:
    print("Waiting for server..")
    data = s.recv(BUFFER_SIZE)
    print(data)
    print("Enter message : ", end="")
    s.send(input().encode('utf-8'))

s.close()
