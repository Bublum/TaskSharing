import json
import os



BUFFER_SIZE = 10240


# 192.168.0.105

def receive_file(sock, file_size, file_name, chunk_size, path):
    file = open(os.path.join(path, file_name), "wb")

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


def my_send(connection, data):
    # print(connection)
    data = json.dumps(data)
    print('send', data)
    connection.send(bytes(data, 'UTF-8'))


def my_recv(connection):
    # print(connection)
    data = connection.recv(BUFFER_SIZE)
    print('recv', data)
    data = json.loads(data.decode('UTF-8'))
    return data


def send_folder(connection, path, type, time_taken=None):
    sizes = []
    # To get sizes of each file
    all_files = os.listdir(path)

    for each in all_files:
        file_info = os.stat(os.path.join(path, each))
        file_size = file_info.st_size
        sizes.append(file_size)

    msg = {
        'type': type,
        'file_size': sizes,
        'chunk_size': BUFFER_SIZE,
        'file_name': all_files,
    }

    if time_taken is not None:
        msg['time_taken'] = time_taken

    my_send(connection, msg)
    print('waiting for acknowledge')
    len(all_files)
    response = my_recv(connection)

    if response['type'] == 'acknowledge_' + type:
        for each in range(len(all_files)):
            file_name = all_files[each]
            f = open(os.path.join(path, file_name), 'rb')
            file_size = sizes[each]
            chunk_size = BUFFER_SIZE

            while file_size > 0:
                print(file_size)
                current = chunk_size
                if file_size < chunk_size:
                    current = file_size
                msg = f.read(current)
                file_size -= current
                connection.send(msg)
            print('Done:' + file_name)

            response = my_recv(connection)
            if not (response['type'] == 'file_received' and response['file_name'] == file_name):
                print('Failure')
                return -1
            else:
                print('Success')
        return 1
    else:
        print('Didn\'t got response', response['type'], type)


def receive_folder(connection, path, received_json, type=None):
    if not os.path.exists(path):
        os.makedirs(path)


    if type is None:
        print('in none')
        response = {'type': received_json['type']}
    else:
        print('in else of none')
        response = {'type': type}
    print(response)
    # connection.send(json.dumps(response).encode('utf-8'))
    my_send(connection, response)
    # response = {'type': received_json['type']}
    # my_send(connection,response)
    chunk_size = received_json["chunk_size"]
    for i in range(len(received_json["file_name"])):
        receive_file(connection, received_json["file_size"][i], received_json["file_name"][i], chunk_size, path)

        file_response = dict()
        file_response["type"] = "file_received"
        file_response["file_name"] = received_json["file_name"][i]

        connection.send(json.dumps(file_response).encode('utf-8'))
        print("received " + received_json["file_name"][i])
    return
