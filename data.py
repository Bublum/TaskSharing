import json
import socket
import netifaces as ni

BUFFER_SIZE = 1024
coordinator_ip = '127.0.0.1'
coordinator_port = 5039


class DataServer:
    def __init__(self, ip, hostname, port):
        self.ip = ip
        self.hostname = hostname
        self.type = 'DataServer'
        self.port = port


def create_init_message(self_hostname, self_ip, self_port):
    return json.dumps({
        'message_type': 'server_metadata',
        'data_server_host_name': self_hostname,
        'data_server_ip': self_ip,
        'data_server_port': self_port
    }).encode('UTF-8')


def create_file_send_message(type, start_frame, end_frame, number_of_bytes, chunk_size):
    return json.dumps({
        'type': type,
        'start_frame': start_frame,
        'end_frame': end_frame,
        'num_of_bytes': number_of_bytes,
        'chunk_size': chunk_size,
    }).encode('UTF-8')


def init_self(port):
    print(ni.interfaces())
    self_ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
    self_hostname = socket.gethostname()
    data_server = DataServer(self_ip, self_hostname, port)
    return data_server


def send_coordinator_init_message(data_server):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((coordinator_ip, coordinator_port))
    init_message = create_init_message(data_server.hostname, data_server.ip, data_server.port)
    s.send(init_message)
    s.close()


message_types = {
    'GET_DATA': ''
}


def send_file(path, client_sock, type):
    print('Sending file')
    try:
        file = open(path, 'r')
        data = file.read(BUFFER_SIZE)
        client_sock.send(
            create_file_send_message(type, '0', '100', number_of_bytes=len(data), chunk_size=BUFFER_SIZE))
        while data:
            client_sock.send(data)
            data = file.read(BUFFER_SIZE)
        file.close()
        client_sock.close()
    except IOError:
        client_sock.send(json.dumps({'error': str(IOError.filename)}).encode('UTF-8'))


if __name__ == '__main__':
    data_server = init_self(5037)
    send_coordinator_init_message(data_server)
    socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_obj.bind((data_server.ip, data_server.port))
    socket_obj.listen(1)
    while 1:
        client_sock, address = socket_obj.accept()
        if client_sock:
            print('Connection with coordinator established.')
            data = client_sock.recv(BUFFER_SIZE)
            data_json = json.loads(data)
            print(data_json)
            if data_json['message_type'] == 'sample_code':
                send_file('test_text_file.txt', client_sock, type='sample_code')
            elif data_json['message_type'] == 'client_code':
                send_file('client_code.py', client_sock, type='client_code')
            elif data_json['message_type'] == 'server_code':
                send_file('server_code.py', client_sock, type='server_code')

            print('Closed connection with coordinator')
