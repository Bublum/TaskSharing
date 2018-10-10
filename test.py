import random
file = open('input_data.txt','wt')
for i in range(100000):
    x = random.randint(1,10000)
    file.write(str(x)+'\n')