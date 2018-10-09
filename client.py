import socket
import os
import subprocess
import json
import time

TCP_IP = '192.168.0.113'
TCP_PORT = 7800
BUFFER_SIZE = 10240
TIMEOUT = 10000000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print("Connected..")


def execute_code(s, filename):
    start = time.time()
    code = subprocess.Popen(["python", filename], stdout=subprocess.PIPE)

    while code.returncode is None:
        # output = code.stdout.readline()
        # s.send(output)
        code.poll()

    end = time.time()

    response = {}
    response['type'] = "assess_result"
    response["time_taken"] = "{:.3f}".format(end - start)

    s.send(json.dumps(response).encode('utf-8'))


while True:
    print("Waiting for server..")
    # s.settimeout(TIMEOUT)
    received = s.recv(BUFFER_SIZE)
    print(received)
    received = received.decode('utf-8')
    data = json.loads(received)
    if data["type"] == "question":
        response = {}
        response['type'] = "introduction"
        response["host"] = socket.gethostname()
        response["role"] = "client"

        s.send(json.dumps(response).encode('utf-8'))

    elif data["type"] == "assess":  # chunksize bytes

        cwd = os.getcwd()
        if not os.path.exists(cwd + '/assess'):
            os.makedirs(cwd + '/assess')
        os.chdir(cwd + '/assess')

        response = {}
        response['type'] = "acknowledge_" + data["type"]

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
                # print('--------' + str(len(file_data)))
                bytes_received -= len(file_data)
                while not file_data:
                    file_data = s.recv(current)
                file.write(file_data)

            file.close()

            file_response = {}
            file_response["type"] = "file_received"
            file_response["file_name"] = data["file_name"][i]

            s.send(json.dumps(file_response).encode('utf-8'))
            print("received " + data["file_name"][i])

        # response = "All received. Executing " + data["file_name"][data["file_type"].index("code")]
        # s.send(response.encode('utf-8'))
        execute_code(s, data['file_name'][data["file_type"].index("code")])
        os.chdir(cwd)


    elif data["type"] == "actual_code":
        pass
    elif data["type"] == "actual_data":
        pass

s.close()
