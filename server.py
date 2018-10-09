import socket
import threading
import os
import json
import math

COUNTER = 0

ASSESS_DIR = os.getcwd() + '/assess/'

DATA_IP = ''
DATA_THREAD_ID = -1
DATA_PORT = 0

HAS_SAMPLE = True
SAMPLE_FILE = ['sample_code.py', 'sample.mkv', 'sample_code2.py']
SAMPLE_TYPE = ['code', 'input', 'input']


HAS_CODE = False

BUFFER_SIZE = 10240  # Normally 1024, but we want fast response


def my_send(connection, data):
    data = json.dumps(data)
    print('send', data)
    connection.send(bytes(data, 'UTF-8'))


def my_recv(connection):
    data = connection.recv(BUFFER_SIZE)
    print('recv', data)
    data = json.loads(data.decode('UTF-8'))
    return data


def get_sample_data():
    global HAS_SAMPLE
    global DATA_IP
    global DATA_PORT
    global HAS_SAMPLE
    HAS_SAMPLE = True
    if DATA_IP == '':
        print('Data node not found')
    else:
        if DATA_PORT != 0:
            msg = {
                'type': 'sample_code',
            }
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((DATA_IP, DATA_PORT))
            my_send(s, msg)
            response = my_recv(s)

            if response['type'] == 'sample_code':
                msg['type'] = "acknowledge_" + response["type"]

                s.send(json.dumps(response).encode('utf-8'))

                chunk_size = response["chunk_size"]

                for i in range(len(response["file_name"])):
                    current = response["file_size"][i]
                    file = open(response["file_name"][i], "wb")

                    while current > 0:

                        current = chunk_size
                        if current < chunk_size:
                            current = current
                        print(current)
                        # s.settimeout(TIMEOUT)
                        file_data = s.recv(current)
                        # print('--------' + str(len(file_data)))
                        current -= len(file_data)
                        while not file_data:
                            file_data = s.recv(current)
                        file.write(file_data)

                    file.close()

                    file_response = {}
                    file_response["type"] = "file_received"
                    file_response["file_name"] = response["file_name"][i]

                    s.send(json.dumps(file_response).encode('utf-8'))
                    print("received " + response["file_name"][i])
                HAS_SAMPLE = True
            else:
                print('Error Occurred')

        else:
            print('Data port not found')


def send_code_files(connection):
    if HAS_CODE:

        cwd = os.getcwd()

        code_path = '/code'

        full_path = cwd + code_path

        sizes = []
        # To get sizes of each file
        file_names = os.listdir(full_path)

        for each in SAMPLE_FILE:
            file_info = os.stat(ASSESS_DIR + '/' + each)
            file_size = file_info.st_size
            sizes.append(file_size)

        msg = {
            'type': 'assess',
            'file_size': sizes,
            'chunk_size': BUFFER_SIZE,
            'file_name': SAMPLE_FILE,
            'file_type': SAMPLE_TYPE
        }
        my_send(connection, msg)
        print('waiting for acknowledge')
        response = my_recv(connection)

        if response['type'] == 'acknowledge_assess':

            for each in range(len(SAMPLE_FILE)):
                file_name = SAMPLE_FILE[each]
                file_type = SAMPLE_TYPE[each]
                f = open(ASSESS_DIR + file_name, 'rb')
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
                else:
                    print('Success')



        else:
            print('Didnt got response')
    else:
        msg = {
            'type': 'error',
            'error': 'Data node not connected'
        }
        my_send(connection, msg)

def assess(connection, address):
    current_dir = os.getcwd()

    if HAS_SAMPLE:

        sizes = []
        # To get sizes of each file
        for each in SAMPLE_FILE:
            file_info = os.stat(ASSESS_DIR + '/' + each)
            file_size = file_info.st_size
            sizes.append(file_size)

        msg = {
            'type': 'assess',
            'file_size': sizes,
            'chunk_size': BUFFER_SIZE,
            'file_name': SAMPLE_FILE,
            'file_type': SAMPLE_TYPE
        }
        my_send(connection, msg)
        print('waiting for acknowledge')
        response = my_recv(connection)

        if response['type'] == 'acknowledge_assess':

            for each in range(len(SAMPLE_FILE)):
                file_name = SAMPLE_FILE[each]
                file_type = SAMPLE_TYPE[each]
                f = open(ASSESS_DIR + file_name, 'rb')
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
                else:
                    print('Success')



        else:
            print('Didnt got response')
    else:
        msg = {
            'type': 'error',
            'error': 'Sample file not found'
        }
        my_send(connection, msg)


class MyThread(threading.Thread):
    fps = 0
    role = ''

    def __init__(self, node):
        global COUNTER
        threading.Thread.__init__(self)
        self.threadID = COUNTER
        self.node = node
        self.connection = node[0]
        self.address = node[1]
        # self.work = work
        COUNTER += 1

    def run(self):
        global HAS_SAMPLE
        global DATA_IP
        global DATA_THREAD_ID
        global DATA_PORT
        msg = {
            'type': 'question',
            'question': 'role'
        }
        my_send(self.connection, data=msg)

        response = my_recv(self.connection)
        role = response['role']
        self.role = role
        print(response)
        print(role)
        if role == 'data_server':

            DATA_IP = self.address
            DATA_THREAD_ID = self.threadID
            msg = {
                'type': 'request',
                'file_type': 'code'
            }

            my_send(self.connection, data=msg)
            response = my_recv(self.connection)

            type = response['type']
            file_name = response['file_name']
            file_size = response['file_size']
            chunk_size = response['chunk_size']

            msg = {
                'type': 'acknowledge_' + type
            }
            my_send(self.connection, data=msg)

            for i in range(len(file_name)):
                file = open('code/' + file_name[i], "wb")
                bytes_received = file_size[i]
                while bytes_received > 0:

                    current = chunk_size
                    if bytes_received < chunk_size:
                        current = bytes_received
                    print(bytes_received)
                    # s.settimeout(TIMEOUT)
                    file_data = self.connection.recv(current)
                    # print('--------' + str(len(file_data)))
                    bytes_received -= len(file_data)
                    file.write(file_data)

                file.close()

                file_response = {
                    "type": "file_received",
                    "file_name": file_name[i]
                }
                my_send(self.connection, data=file_response)
                print("received " + file_name[i])

            self.connection.close()
        else:
            # assess(self.connection, self.address)
            final_answer = 'yes'
            while final_answer == 'yes':
                send_code_files()
            self.connection.close()


hostname = socket.gethostname()
import netifaces as ni

# ni.ifaddresses('wlp3s0')
# ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
# print(ip)
print("Your Computer Name is:" + hostname)
TCP_IP = input("Enter IP: ")

TCP_PORT = int(input("Enter Port greater than 1200: "))
while TCP_PORT < 1200:
    TCP_PORT = int(input("Enter Port greater than 1200: "))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(100)

while True:
    print('Waiting for new connection: ')
    node = s.accept()
    print('New Request from address:', node)
    MyThread(node).start()
