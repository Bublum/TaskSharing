file = open('/home/anish/PycharmProjects/TaskSharing/actual/data/input_data.txt','rt')
numbers = []
data = file.readline()
while data:
    numbers.append(int(data))
    data = file.readline()
file.close()
print(max(numbers))