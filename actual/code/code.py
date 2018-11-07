import os
import time

path = os.getcwd()
file = open(path + '/actual/input.txt', 'rt')
numbers = []
data = file.readline()
while data:
    numbers.append(int(data))
    data = file.readline()
file.close()
# time.sleep(0.5)
if not os.path.exists(os.path.join(os.path.join(path, 'actual'), 'output')):
    os.mkdir(os.path.join(os.path.join(path, 'actual'), 'output'))

file = open(os.path.join(os.path.join(os.path.join(path, 'actual'), 'output'), 'output.txt'), 'w')

file.write(str(max(numbers)))
