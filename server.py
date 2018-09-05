import socket
import threading
import os
import json
import math

COUNTER = 0

ASSESS_DIR = os.getcwd() + '/assess'

DATA_IP = ''
DATA_THREAD_ID = -1
DATA_PORT = 0

HAS_SAMPLE = True
SAMPLE_FILE = ['sample_code.py','test.mkv','sample_code2.py']
SAMPLE_TYPE = ['code','input','input']

BUFFER_SIZE = 10240  # Normally 1024, but we want fast response


def my_send(connection, data):
    data = json.dumps(data)
    print(data)
    connection.send(bytes(data, 'UTF-8'))


def get_sample_data():
    global HAS_SAMPLE
    global DATA_IP
    global DATA_PORT
    if DATA_IP == '':
        print('Data node not found')
    else:
        if DATA_PORT != 0:
            msg = {
                'type': 'sample_code',

            }
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TCP_IP, TCP_PORT))
            json.dump(msg, s)
            response = s.recv(BUFFER_SIZE)
            response = json.load(response)
            if response['type'] == 'sample_code':
                chunk_size = int(response['chunk_size'])
                num_of_bytes = int(response['num_of_bytes'])
                number = math.ceil(num_of_bytes / chunk_size)
                f = open("sample_code.py", "w")
                for i in range(number):
                    response = s.recv(BUFFER_SIZE)
                    f.write(response)
                HAS_SAMPLE = True
            else:
                print('Error Occurred')

        else:
            print('Data port not found')


def assess(connection, address):
    current_dir = os.getcwd()

    if HAS_SAMPLE:

        sizes = []
        #To get sizes of each file
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

        for each in range(len(SAMPLE_FILE)):
            file_name = SAMPLE_FILE[each]
            file_type =

        f = open(ASSESS_DIR + '/' + SAMPLE_CODE, 'rb')
        file_info = os.stat(ASSESS_DIR + '/' + SAMPLE_CODE)
        file_size = file_info.st_size
        data_info = os.stat(ASSESS_DIR + '/' + SAMPLE_DATA)
        data_size = data_info.st_size
        file_name = [SAMPLE_CODE, SAMPLE_DATA]
        file_arr = [file_size, data_size]
        chunk_size = BUFFER_SIZE

        my_send(connection, msg)

        while file_size > 0:

            current = 0
            if file_size < chunk_size:
                current = file_size
            else:
                current = chunk_size
            print(current)
            msg = f.read(current)
            file_size -= current
            connection.send(msg)

        f = open(ASSESS_DIR + '/' + SAMPLE_DATA, 'rb')
        print(data_size)
        print(data_size / BUFFER_SIZE)
        while data_size > 0:

            current = 0
            if data_size < chunk_size:
                current = data_size
            else:
                current = chunk_size
            print(current)
            msg = f.read(current)
            data_size -= current
            connection.send(msg)

        print('Done')


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
        COUNTER += 1

    def run(self):
        global HAS_SAMPLE
        global DATA_IP
        global DATA_THREAD_ID
        global DATA_PORT
        msg = {
            'type': 'question',
            'question': 'Role'
        }
        my_send(self.connection, data=msg)

        response = self.connection.recv(BUFFER_SIZE)
        response = json.loads(response.decode('UTF-8'))
        role = response['role']
        self.role = role
        print(response)
        print(role)
        if role == 'data':
            DATA_IP = self.address
            DATA_THREAD_ID = self.threadID
            self.connection.close()
        else:
            assess(self.connection, self.address)
            # self.connection.close()


hostname = socket.gethostname()
import netifaces as ni

ni.ifaddresses('wlp3s0')
ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
print(ip)
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
