import time

start = time.time()

while time.time() <= start+2:
    print("Waiting..")
print(time.time() - start)