import socket
import os
import subprocess
import json
import time

TCP_IP = '192.168.0.113'
TCP_PORT = 7800
BUFFER_SIZE = 10240
TIMEOUT = 10000000


def execute_code(filename):
    start = time.time()
    code = subprocess.Popen(["python3", filename], stdout=subprocess.PIPE)

    while code.returncode is None:
        # output = code.stdout.readline()
        # s.send(output)
        code.poll()
    end = time.time()
    return "{:.3f}".format(end - start)


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


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    print("Connected..")

    while True:
        print("Waiting for server..")
        received = s.recv(BUFFER_SIZE)
        print(received)
        received = received.decode('utf-8')
        data = json.loads(received)

        if data["type"] == "question":
            response = dict()
            response['type'] = "introduction"
            response["host"] = socket.gethostname()
            response["role"] = "client"

            s.send(json.dumps(response).encode('utf-8'))

        elif data["type"] == "assess":
            cwd = os.getcwd()
            if not os.path.exists(cwd + '/' + data['type']):
                os.makedirs(cwd + '/' + data['type'])
            os.chdir(cwd + '/' + data['type'])

            response = {'type': "acknowledge_" + data["type"]}
            s.send(json.dumps(response).encode('utf-8'))

            chunk_size = data["chunk_size"]

            for i in range(len(data["file_name"])):
                bytes_received = data["file_size"][i]
                file = open(data["file_name"][i], "wb")

                while bytes_received > 0:

                    current = chunk_size
                    if bytes_received < chunk_size:
                        current = bytes_received
                    print(bytes_received)
                    # s.settimeout(TIMEOUT)
                    file_data = s.recv(current)
                    bytes_received -= len(file_data)
                    while not file_data:
                        file_data = s.recv(current)
                    file.write(file_data)

                file.close()

                file_response = dict()
                file_response["type"] = "file_received"
                file_response["file_name"] = data["file_name"][i]

                s.send(json.dumps(file_response).encode('utf-8'))
                print("received " + data["file_name"][i])

            # response = "All received. Executing " + data["file_name"][data["file_type"].index("code")]
            # s.send(response.encode('utf-8'))
            # execute_code(s, data['file_name'][data["file_type"].index("code")])
            os.chdir(cwd)

        elif data["type"] == "actual":
            cwd = os.getcwd()
            if not os.path.exists(cwd + '/' + data['type']):
                os.makedirs(cwd + '/' + data['type'])
            os.chdir(cwd + '/' + data['type'])

            response = {'type': "acknowledge_" + data["type"]}
            s.send(json.dumps(response).encode('utf-8'))

            chunk_size = data["chunk_size"]
            for i in range(len(data["file_name"])):
                receive_file(s, data["file_size"][i], data["file_name"][i], chunk_size)

                file_response = dict()
                file_response["type"] = "file_received"
                file_response["file_name"] = data["file_name"][i]

                s.send(json.dumps(file_response).encode('utf-8'))
                print("received " + data["file_name"][i])

            response = {'type': "acknowledge_" + data["type"]}
            s.send(json.dumps(response).encode('utf-8'))
            os.chdir(cwd)

        elif data["type"] == "actual_input":
            print("Do you want to continue(y/n): ", end="")
            choice = 'n'
            start_time = time.time()
            while time.time() <= start_time + 5:
                choice = input()

            if choice == 'n':
                print("Closing Connection.....")
            else:
                response = {'type': "response_input", 'response:': input('')}
                s.send(json.dumps(response).encode('utf-8'))

                cwd = os.getcwd()
                if not os.path.exists(cwd + '/actual'):
                    os.makedirs(cwd + '/actual')
                os.chdir(cwd + '/actual')

                chunk_size = data["chunk_size"]
                for i in range(len(data["file_name"])):
                    receive_file(s, data["file_size"][i], data["file_name"][i], chunk_size)

                    file_response = dict()
                    file_response["type"] = "file_received"
                    file_response["file_name"] = data["file_name"][i]

                    s.send(json.dumps(file_response).encode('utf-8'))
                    print("received " + data["file_name"][i])

        elif data["type"] == "error":
            pass

