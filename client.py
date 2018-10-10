import select
import signal
import socket
import os
import subprocess
import json
import sys
import time
import general

TCP_IP = '192.168.0.105'
TCP_PORT = int(input('Enter Port: '))
BUFFER_SIZE = 10240
TIMEOUT = 5  # for input()


def execute_code(path):
    start = time.time()
    # code = subprocess.Popen(["python3", path], stdout=subprocess.PIPE)
    try:
        code = subprocess.check_call(["python3", path], stdout=subprocess.PIPE)

        # while code.returncode is None:
        #     # output = code.stdout.readline()
        #     # s.send(output)
        #     code.poll()
        end = time.time()
        return "{:.3f}".format(end - start)

    except subprocess.CalledProcessError:
        return "FAIL"


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
            if data["question"] == "role":
                response = dict()
                response['type'] = "introduction"
                response["host"] = socket.gethostname()
                response["role"] = "client"

                s.send(json.dumps(response).encode('utf-8'))

            elif data["question"] == "input_data":

                print("Do you want to continue(y/n): ", end="")
                sys.stdout.flush()
                choice = 'y'
                # start_time = time.time()

                i, o, e = select.select([sys.stdin], [], [], TIMEOUT)

                if (i):
                    choice = sys.stdin.readline().strip()
                else:
                    choice = 'y'

                response = {'type': "response_input"}
                if choice == 'n':
                    response['response'] = 'no'
                    s.send(json.dumps(response).encode('utf-8'))
                    print("Closing Connection.....")
                    s.close()
                    exit()
                else:
                    response['response'] = 'yes'
                    s.send(json.dumps(response).encode('utf-8'))

        elif data["type"] == "assess":
            cwd = os.getcwd()
            path = os.path.join(cwd, data['type'])
            general.receive_folder(s, path, data, "acknowledge_assess")

        elif data["type"] == "actual_code":
            cwd = os.getcwd()
            path = os.path.join(cwd, 'actual')
            general.receive_folder(s, path, data, "acknowledge_actual_code")

        elif data["type"] == "actual_input":
            cwd = os.getcwd()
            path = os.path.join(cwd, 'actual')

            general.receive_folder(s, path, data, "acknowledge_actual_input")

            code_file_path = os.path.join(path, 'code.py')
            output_path_join = os.path.join(path, 'output')

            time.sleep(1)
            time_taken = execute_code(code_file_path)

            if time_taken == "FAIL":
                response = {'type': 'finished', 'status': 'failure'}
                s.send(json.dumps(response).encode('utf-8'))

            else:
                response = {'type': 'finished', 'status': 'success'}
                s.send(json.dumps(response).encode('utf-8'))

            print("Waiting for server..")
            received = s.recv(BUFFER_SIZE)
            print(received)
            received = received.decode('utf-8')
            data = json.loads(received)

            if data["type"] == "acknowledge_finished" and time_taken != "FAIL":
                general.send_folder(s, output_path_join, "result", time_taken)

        elif data["type"] == "error":
            print("Error" + data['error'])


main()
