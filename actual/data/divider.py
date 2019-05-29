import os

cwd = os.getcwd()

file_name = 'input_data.txt'

path = cwd + '/' + file_name

output_path = cwd + '/input/'

f = open(path, 'r')

batch_size = 1000


def create_folder(path, file_name, data):
    if not os.path.exists(path):
        os.makedirs(path)
    f = open(path + file_name,'w')
    for each in data:
        f.write(each)
    f.close()


counter = 0
data = []
index = 0
extension = '.txt'

for each in f:
    counter += 1
    data.append(each)
    if counter == batch_size:
        counter = 0
        create_folder(output_path + str(index) + '/', 'input' + extension, data)
        data = []
        index += 1
