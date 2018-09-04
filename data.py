import json
import socket
import netifaces as ni
import os
import cv2
import pickle

BUFFER_SIZE = 1024


def send_sample_code(path, client_sock):
    size = os.path.getsize(path)
    client_sock.send(create_sample_code_message('sample', '0', '100', number_of_bytes=size, chunk_size=BUFFER_SIZE))
    file = open(path, 'r')

    data = file.read(BUFFER_SIZE)
    while file:
        client_sock.send(data)
        data = file.read(BUFFER_SIZE)
    file.close()
    client_sock.close()


class DataServer:
    def __init__(self, ip, hostname, port):
        self.ip = ip
        self.hostname = hostname
        self.type = 'DataServer'
        self.port = port


coordinator_ip = '192.168.0.109'
coordinator_port = 5600


def create_message(self_hostname, self_ip, self_port):
    return {
        'type': 'data',
        'data_host_name': self_hostname,
        'data_ip': self_ip,
        'data_port': self_port
    }


def create_sample_code_message(type, start_frame, end_frame, number_of_bytes, chunk_size):
    return {
        'type': type,
        'start_frame': start_frame,
        'end_frame': end_frame,
        'num_of_bytes': number_of_bytes,
        'chunk_size': chunk_size,
    }


def init_self(port):
    self_ip = ni.ifaddresses('wlp2s0')[ni.AF_INET][0]['addr']
    self_hostname = socket.gethostname()
    data_server = DataServer(self_ip, self_hostname, port)
    return data_server


def init(data_server):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((data_server.ip, data_server.port))
    s.connect((coordinator_ip,coordinator_port))
    init_message = json.dumps(create_message(data_server.hostname, data_server.ip, data_server.port))
    s.send(init_message.encode('UTF-8'))
    return s


message_types = {
    'GET_DATA': ''
}

if __name__ == '__main__':
    data_server = init_self(5037)
    socket_obj = init(data_server)
    socket_obj.listen(1)
    while 1:
        client_sock, address = socket_obj.accept()
        if client_sock:
            data = client_sock.recv(BUFFER_SIZE)
            data_json = json.loads(data)
            print(data_json)
            if data_json['MESSAGE_TYPE'] == 'SAMPLE_CODE':
                send_sample_code('test_text_file.txt', client_sock)
