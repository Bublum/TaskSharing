import json
import socket

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 200  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print('Connection address:' + str(addr))
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data: break
    print("received data:" + str(data))
    conn.send('HTTP/1.1 200 OK\n'
              'Connection: close\n'
              'Content-Type: text/html\n'
              '\n'
              +json.dumps(all_folders).encode('UTF-8'))
    # conn.send(data)  # echo
conn.close()
