import socket
import subprocess
import json

TCP_IP = '192.168.0.109'
TCP_PORT = 8600
BUFFER_SIZE = 10240

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print("Connected..")


def execute_code(s, filename):
    code = subprocess.Popen(["python", filename], stdout=subprocess.PIPE)

    while code.returncode is None:
        output = code.stdout.readline()
        print(output)
        print("-"*20)
        s.send(output)
        code.poll()

    s.send("Done".encode('utf-8'))


while True:
    print("Waiting for server..")
    data = json.loads(s.recv(BUFFER_SIZE).decode('utf-8'))
    print(data)
    if data["type"] == "question":
        response = {}
        response['type'] = "introduction"
        response["host"] = socket.gethostname()
        response["role"] = "client"

        s.send(json.dumps(response).encode('utf-8'))

    elif data["type"] == "assess":  # chunksize bytes
        chunk_size = data["chunk_size"]

        for i in range(len(data["file_name"])):
            bytes_received = 0
            file = open(data["file_name"][i], "wb")

            while bytes_received != data["file_size"][i]:
                file_data = s.recv(chunk_size)
                file.write(file_data)
                bytes_received += len(file_data)

            file.close()
            print("received " + str(bytes_received) + " bytes as " + data["file_name"][i])

        response = "All received. Executing " + data["file_name"][data["file_type"].index("code")]
        s.send(response.encode('utf-8'))
        #execute_code(s, data['file_name'][data["file_type"].index("code")])


    elif data["type"] == "actual_code":
        pass
    elif data["type"] == "actual_data":
        pass

s.close()
