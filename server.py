import socket
import threading
import os
import json
import queue
import math

from general import my_send, my_recv, send_folder, receive_folder

COUNTER = 0

ASSESS_DIR = os.getcwd() + '/assess/'

DATA_IP = ''
DATA_THREAD_ID = -1
DATA_PORT = 0

HAS_SAMPLE = True
SAMPLE_FILE = ['sample_code.py', 'sample.mkv', 'sample_code2.py']
SAMPLE_TYPE = ['code', 'input', 'input']

HAS_CODE = True

BUFFER_SIZE = 10240  # Normally 1024, but we want fast response

task_queue = queue.Queue()  # stores list of tasks
done_task_list = []  # takes data from data_server and appends its metadata it into this list.


# def get_sample_data():
#     global HAS_SAMPLE
#     global DATA_IP
#     global DATA_PORT
#     global HAS_SAMPLE
#     HAS_SAMPLE = True
#     if DATA_IP == '':
#         print('Data node not found')
#     else:
#         if DATA_PORT != 0:
#             msg = {
#                 'type': 'sample_code',
#             }
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.connect((DATA_IP, DATA_PORT))
#             my_send(s, msg)
#             response = my_recv(s)
#
#             if response['type'] == 'sample_code':
#                 msg['type'] = "acknowledge_" + response["type"]
#
#                 s.send(json.dumps(response).encode('utf-8'))
#
#                 chunk_size = response["chunk_size"]
#
#                 for i in range(len(response["file_name"])):
#                     current = response["file_size"][i]
#                     file = open(response["file_name"][i], "wb")
#
#                     while current > 0:
#
#                         current = chunk_size
#                         if current < chunk_size:
#                             current = current
#                         print(current)
#                         # s.settimeout(TIMEOUT)
#                         file_data = s.recv(current)
#                         # print('--------' + str(len(file_data)))
#                         current -= len(file_data)
#                         while not file_data:
#                             file_data = s.recv(current)
#                         file.write(file_data)
#
#                     file.close()
#
#                     file_response = {"type": "file_received", "file_name": response["file_name"][i]}
#
#                     s.send(json.dumps(file_response).encode('utf-8'))
#                     print("received " + response["file_name"][i])
#                 HAS_SAMPLE = True
#             else:
#                 print('Error Occurred')
#
#         else:
#             print('Data port not found')


def send_code_files(connection):
    if HAS_CODE:
        cwd = os.getcwd()

        code_path = '/code'

        full_path = cwd + code_path + '/'
        send_folder(connection, full_path, 'actual_code')

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
        self.number = 0

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
            # print(self.address)
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
                # print(self.address)
                my_send(self.connection, data=file_response)
                print("received " + file_name[i])
            global HAS_CODE
            HAS_CODE = True
            while True:
                # print(task_queue.empty())
                if not task_queue.empty():
                    each_task = task_queue.get()
                    if each_task['type'] == 'send_output':
                        each_task['type'] = 'output'

                    # print(self.address)
                    my_send(self.connection, data=each_task)
                    response = my_recv(self.connection)

                    type = response['type']



                    if type == 'get_input':
                        msg = {
                            'type': 'acknowledge_' + type
                        }
                        # print(self.address)
                        my_send(self.connection, data=msg)
                        file_names = response['file_name']
                        file_size = response['file_size']
                        chunk_size = response['chunk_size']
                        path = 'input/' + str(each_task['client_id']) + '/' + str(each_task['number']) + '/'
                        if not os.path.exists(path):
                            os.makedirs(path)

                        # receive_folder(self.connection, path, response)
                        for i in range(len(file_names)):
                            file = open(path +
                                        file_names[i], "wb")
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
                                "file_name": file_names[i]
                            }
                            # print(self.address)
                            my_send(self.connection, data=file_response)
                            print("received " + file_names[i] + ' for client/number ' + str(each_task['client_id']) +
                                  '/' + str(each_task['number']))
                        folder_path = os.getcwd() + '/input/' + str(each_task['client_id']) + '/' + \
                                      str(each_task['number']) + '/'

                        done_task = {
                            str(each_task['client_id']) + '_' + str(each_task['number']): {
                                'file_names': file_names,
                                'folder_path': folder_path,
                                'status': 'done'
                            }
                        }

                        done_task_list.append(done_task)
                    elif type == 'acknowledge_output':
                        msg = {
                            'type': type
                        }
                        # print(self.address)
                        # my_send(self.connection, data=msg)
                        each_task['chunk_size'] = BUFFER_SIZE
                        send_folder(self.connection, each_task['path'], 'output_files')
                        # my_recv(self.connection)
                        print("folder sent! path:  " + each_task['path'])

                # self.connection.close()
        else:
            # assess(self.connection, self.address)
            final_answer = 'yes'
            send_code_files(connection=self.connection)
            while final_answer == 'yes':

                request = {
                    'type': 'question',
                    'question': 'input_data'
                }
                # print(self.address)
                my_send(self.connection, request)

                response = my_recv(self.connection)

                if response['type'] == 'response_input':
                    final_answer = response['response']
                    if response['response'] == 'yes':
                        print('Got yes')
                        my_dict = {
                            'client_id': self.threadID,
                            'number': self.number,
                            'type': 'get_input'
                        }
                        task_queue.put(my_dict)
                        exists = False
                        msg = str(self.threadID) + '_' + str(self.number)
                        index = -1
                        while not exists:
                            length = done_task_list.__len__()
                            for i in range(length):
                                if msg in done_task_list[i]:
                                    exists = True
                                    index = i
                                    break
                        current_task = done_task_list[index][msg]

                        send_folder(self.connection, current_task['folder_path'], 'actual_input')

                        recv_response = my_recv(self.connection)
                        while not recv_response:
                            recv_response = my_recv(self.connection)
                        if recv_response['type'] == 'finished':
                            temp_response = {
                                'type': 'acknowledge_' + recv_response['type']
                            }
                            # print(self.address)
                            my_send(self.connection, temp_response)
                            if recv_response['status'] == 'success':
                                path = os.getcwd() + '/output/' + str(self.threadID) + '_' + str(self.number)
                                response = my_recv(self.connection)
                                response['type'] = 'acknowledge_' + response['type']
                                receive_folder(self.connection, path, response)
                                task_json = {
                                    'client_id': self.threadID,
                                    'number': self.number,
                                    'type': 'send_output',
                                    'path': path
                                }
                                task_queue.put(task_json)
                                print('Inserted into task')

                        else:
                            print('Got type not finished')
                        self.number += 1
                    else:
                        print('got NO')

            self.connection.close()
            return 1


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
