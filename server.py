import socket
import threading

counter = 0


# def node_assesser(conn):

class MyThread(threading.Thread):
    def __init__(self, threadID, node):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.node = node

    def run(self):
        print("Starting " + str(self.node[1]))
        accept_data(self.node)
        print("Exiting " + str(self.node[0]))


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

BUFFER_SIZE = 200  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(100)


def accept_data(node):
    global counter
    print("Welcome! Type Your message: ")
    while 1:

        msg = str(counter)
        counter += 1

        node[0].send(msg.encode('UTF-8'))

        data = node[0].recv(BUFFER_SIZE)
        if not data: break
        print("received data:", data)
        # node[0].send(data)
    node[0].close()


while True:
    print('Waiting for new connection: ')
    node = s.accept()
    print('New Request from address:', node)
    MyThread(accept_data, node).start()
