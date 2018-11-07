import json
import os
import socket
import netifaces as ni
import subprocess
import _thread
import time

from general import my_recv, my_send, send_folder, receive_folder

BUFFER_SIZE = 1024
server_ip = '192.168.43.154'
server_port = int(input('Enter port'))

folder_names = os.listdir(os.getcwd() + '/actual/data/input')
all_folders = []
for name in folder_names:
    folder_info = {
        'folder': name,
        'status': 'no',
        'uid': '',
        'success': 'yes'
    }
    all_folders.append(folder_info)


# print(all_folders)


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
    #self_ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
    self_ip = '10.31.0.5'
    self_hostname = socket.gethostname()
    data_server = DataServer(self_ip, self_hostname, port)
    return data_server

def receive_file(sock, file_size, file_name, chunk_size):
    file = open(file_name, "wb")

    while file_size > 0:
        current = chunk_size
        if file_size < chunk_size:
            current = file_size
        print(file_size)
        file_data = sock.recv(current)
        file_size -= len(file_data)
        while not file_data:
            file_data = sock.recv(current)
        file.write(file_data)

    file.close()
    return


def send_coordinator_init_message():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    server_query = my_recv(s)
    print('Request from server : ' + str(server_query))
    if server_query['type'] == 'question' and server_query['question'] == 'role':
        my_send(s, {'type': 'question',
                    'role': 'data_server'})
        server_q = my_recv(s)
        if server_q['type'] == 'request' and server_q['file_type'] == 'code':
            send_folder_old('/actual/code', s, type='actual_codes')

    else:
        my_send(s, {'type': 'question',
                    'error': 'invalid_query'})

    return s



message_types = {
    'GET_DATA': ''
}


# def send_file(path, client_sock, type):
#     print('Sending file')
#     try:
#         file = open(path, 'r')
#         data = file.read(BUFFER_SIZE)
#         my_send(client_sock, {
#             'type': type,
#             'file_names': '0',
#             'file_sizes': '100',
#             'num_of_bytes': len(data),
#             'chunk_size': BUFFER_SIZE,
#         })
#         while data:
#             client_sock.send(data)
#             data = file.read(BUFFER_SIZE)
#         file.close()
#         client_sock.close()
#     except IOError:
#         client_sock.send(json.dumps({'error': str(IOError.filename)}).encode('UTF-8'))


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


def send_input(connection, path, data_json):
    type = data_json['type']
    print('input path is : ' + path)
    found = False
    index = 0
    for each in all_folders:
        if each['status'] == 'no':
            found = True
            break
        index += 1
    if found:
        path = path + '/' + all_folders[index]['folder']
        all_folders[index]['status'] = 'processing'
        all_folders[index]['uid'] = str(data_json['client_id']) + '_' + str(data_json['number'])
        send_folder(connection, path, type)
    else:
        print('All folders sent')





def send_folder_old(path, client_sock, type):
    print('Sending files in the folder')
    print(path)
    print(type)
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
                    # print(data)
                    data = file.read(BUFFER_SIZE)
                file.close()
                print('----------Done sending file {}'.format(filename))
                ack_j = my_recv(client_sock)
                if ack_j['type'] == 'file_received':
                    continue
                else:
                    print('ACK NOT RECVD')
                    break


        else:
            print('------------------Did not receive ack------------------')

    except IOError:
        print(IOError.strerror)
        print('send_folder()')


def execute_code(s, filename):
    code = subprocess.Popen(["python", filename], stdout=subprocess.PIPE)

    while code.returncode is None:
        # output = code.stdout.readline()
        # s.send(output)
        code.poll()

    s.send("Done".encode('utf-8'))


debug_receive = 'request received : '


def request_handler(name, delay):
    print('started thread')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('192.168.43.245', 7800))
    s.listen(100)
    while True:
        conn, addr = s.accept()
        print(addr)
        req = conn.recv(BUFFER_SIZE).decode('UTF-8')
        print(req)

        json_data = json.dumps(all_folders)

        conn.send(('HTTP/1.1 200 OK\n'
                   'Connection: close\n'
                   'Content-Type: application/json\n'
                   'Access-Control-Allow-Origin: *\n'
                   'Access-Control-Expose-Headers: Access-Control-Allow-Origin\n'
                   'Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept\n'
                   '\n' +
                   json_data).encode('utf-8'))


_thread.start_new_thread(request_handler, ('akshay', 1))

# data_server = init_self(7443)
s = send_coordinator_init_message()
while True:
    print('\n\nWaiting for connection...')
    # client_sock, address = socket_obj.accept()
    data_json = my_recv(s)
    # print(data_json)
    if data_json:
        if data_json['type'] == 'get_input':
            # print(debug_receive + 'input')
            print('get_input')
            send_input(s, os.getcwd() + '/actual/data/input', data_json)
        elif data_json['type'] == 'output':
            # print(debug_receive + 'output')
            folder_info = data_json
            uid = str(folder_info['client_id']) + '_' + str(folder_info['number'])
            print('uid is : ' + uid)
            # all_folders
            for folders in all_folders:
                print(folders)
                if folders['uid'] == uid:
                    print('changing folders dict : ' + str(folders))
                    folders['status'] = 'done'
                    print('output folder received : ' + str(uid))
                    break
            my_send(s, {'type': 'acknowledge_output'})
            recv_json = my_recv(s)

            receive_folder(s, 'output/' + str(folder_info['client_id']) + '_' + str(folder_info['number']),
                           recv_json, type='acknowledge_output_files')

        elif data_json['type'] == 'request':
            print(debug_receive + 'actual code')
            if data_json['file_type'] == 'code':
                send_folder_old('/actual/code', s, type='actual_codes')
        elif data_json['type'] == 'question':
            print(debug_receive + 'role')
            if data_json['question'] == 'role':
                s.send(json.dumps({'type': 'question',
                                   'role': 'data_server'}).encode('UTF-8'))
        print('Task Completed')
        print(all_folders)
    else:
        print('In else')

