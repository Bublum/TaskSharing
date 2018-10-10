import select, sys

i, o, e = select.select([sys.stdin], [], [], 2)

if (i):
  print("You said", sys.stdin.readline().strip())
else:
  print("You said nothing!")
