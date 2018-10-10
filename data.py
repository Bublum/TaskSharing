import json
import os
import socket
import netifaces as ni
import subprocess

BUFFER_SIZE = 1024
server_ip = '192.168.0.106'
server_port = 9000

input_request_counter = 0
sent_folders = []


class DataServer:
    def __init__(self, ip, hostname, port):
        self.ip = ip
        self.hostname = hostname
        self.type = 'DataServer'
        self.port = port


def create_init_message(self_hostname, self_ip, self_port):
    return json.dumps({
        'type': 'server_metadata',
        'data_server_host_name': self_hostname,
        'data_server_ip': self_ip,
        'data_server_port': self_port
    }).encode('UTF-8')


def init_self(port):
    print(ni.interfaces())
    self_ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
    self_hostname = socket.gethostname()
    data_server = DataServer(self_ip, self_hostname, port)
    return data_server


def my_send(connection, data):
    data = json.dumps(data)
    print(data)
    connection.send(bytes(data, 'UTF-8'))


def my_recv(connection):
    data = connection.recv(BUFFER_SIZE)
    print(data)
    data = json.loads(data.decode('UTF-8'))
    return data


def send_coordinator_init_message():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    server_query = my_recv(s)
    if server_query['type'] == 'question' and server_query['question'] == 'role':
        my_send(s, {'type': 'question',
                    'role': 'data_server'})
        server_q = my_recv(s)
        if server_q['type'] == 'request' and server_q['file_type'] == 'code':
            send_folder_old('/actual/code', s, type='actual_codes')

    else:
        my_send(s, {'type': 'question',
                    'error': 'invalid_query'})
    s.close()


message_types = {
    'GET_DATA': ''
}


def send_file(path, client_sock, type):
    print('Sending file')
    try:
        file = open(path, 'r')
        data = file.read(BUFFER_SIZE)
        my_send(client_sock, {
            'type': type,
            'file_names': '0',
            'file_sizes': '100',
            'num_of_bytes': len(data),
            'chunk_size': BUFFER_SIZE,
        })
        while data:
            client_sock.send(data)
            data = file.read(BUFFER_SIZE)
        file.close()
        client_sock.close()
    except IOError:
        client_sock.send(json.dumps({'error': str(IOError.filename)}).encode('UTF-8'))


def get_file_sizes(file_names, path):
    size_list = []
    for file in file_names:
        size_list.append(os.stat(os.getcwd() + path + '/{}'.format(file)).st_size)
    return size_list


def get_file_types(file_names):
    types = []
    for file in file_names:
        types.append(file.split('.')[1])
    return types


def send_input(connection, path, type):
    all_folders = os.listdir(path)
    left_folders = [x for x in all_folders if x not in sent_folders]
    if left_folders:
        path = path + '/' + left_folders[0]
        sent_folders.append(left_folders[0])
        send_folder(connection, path, type)
    else:
        print('All folders sent')


def send_folder(connection, path, type):
    # cwd = os.getcwd()

    # code_path = '/code'

    # full_path = cwd + code_path + '/'

    sizes = []
    # To get sizes of each file
    all_files = os.listdir(path)

    for each in all_files:
        file_info = os.stat(path + each)
        file_size = file_info.st_size
        sizes.append(file_size)




    msg = {
        'type': type,
        'file_size': sizes,
        'chunk_size': BUFFER_SIZE,
        'file_name': all_files,
    }
    my_send(connection, msg)
    print('waiting for acknowledge')
    response = my_recv(connection)

    if response['type'] == 'acknowledge_actual':

        for each in range(len(all_files)):
            file_name = all_files[each]
            # file_type = SAMPLE_TYPE[each]
            f = open(path + file_name, 'rb')
            file_size = sizes[each]
            chunk_size = BUFFER_SIZE

            while file_size > 0:
                print(file_size)
                current = chunk_size
                if file_size < chunk_size:
                    current = file_size
                # print(current)
                msg = f.read(current)
                file_size -= current
                connection.send(msg)
                # temp = connection.recv(2).decode('UTF-8')
                # print(temp)
                # if temp != 'ok':
                #     print('FAIL')
            print('Done:' + file_name)

            response = my_recv(connection)
            if not (response['type'] == 'file_received' and response['file_name'] == file_name):
                print('Failure')
                return -1
            else:
                print('Success')
                return 1
    else:
        print('Didnt got response')


def send_folder_old(path, client_sock, type):
    print('Sending files in the folder')
    try:
        file_names = os.listdir(os.getcwd() + path)
        file_sizes = get_file_sizes(file_names, path)
        file_types = get_file_types(file_names)
        my_send(client_sock, {
            'type': type,
            'file_name': file_names,
            'file_size': file_sizes,
            'chunk_size': BUFFER_SIZE,
            'file_type': file_types
        })
        ack_json = json.loads(client_sock.recv(BUFFER_SIZE))
        if ack_json['type'] == 'acknowledge_actual_codes':
            total_files = len(os.listdir(os.getcwd() + path))
            for idx, filename in enumerate(os.listdir(os.getcwd() + path)):
                print('File {0} of {1}'.format(idx, total_files))
                file = open(os.getcwd() + path + '/' + filename, 'r')
                data = file.read(BUFFER_SIZE)
                while data:
                    client_sock.send(data.encode('UTF-8'))
                    print(data)
                    data = file.read(BUFFER_SIZE)
                file.close()
                print('----------Done sending file {}'.format(filename))
                ack_j = my_recv(client_sock)
                if ack_j['type'] == 'file_received':
                    continue
                else:
                    print('ACK NOT RECVD')
                    break

            # client_sock.close()
        else:
            print('------------------Did not receive ack------------------')
            client_sock.close()
    except IOError:
        print(IOError.strerror)
        print('send_folder()')
        # client_sock.send(json.dumps({'error': str(IOError.filename)}).encode('UTF-8'))
        client_sock.close()


def execute_code(s, filename):
    code = subprocess.Popen(["python", filename], stdout=subprocess.PIPE)

    while code.returncode is None:
        # output = code.stdout.readline()
        # s.send(output)
        code.poll()

    s.send("Done".encode('utf-8'))


if __name__ == '__main__':
    data_server = init_self(7443)
    send_coordinator_init_message()
    socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_obj.bind((data_server.ip, data_server.port))
    socket_obj.listen(1)
    while 1:
        print('Waiting for connection...')
        client_sock, address = socket_obj.accept()
        if client_sock:
            print('Connection with coordinator established.')
            data = client_sock.recv(BUFFER_SIZE)
            data_json = json.loads(data)
            print(data_json)
            if data_json['type'] == 'sample_code':
                send_file('test_text_file.txt', client_sock, type='sample_code')
            elif data_json['type'] == 'client_code':
                send_file('client_code.py', client_sock, type='client_code')
            elif data_json['type'] == 'server_code':
                send_file('server_code.py', client_sock, type='server_code')
            elif data_json['type'] == 'input':
                send_input(client_sock, os.getcwd() + '/input', data_json['type'])

            # elif data_json['type'] == 'request':
            #     print('request')
            #     if data_json['file_type'] == 'code':
            #         send_folder('/actual/code', client_sock, type='actual_codes')
            # elif data_json['type'] == 'question':
            #     if data_json['question'] == 'role':
            #         client_sock.send(json.dumps({'type': 'question',
            #                                      'role': 'data_server'}).encode('UTF-8'))
            print('Closed connection with coordinator')
