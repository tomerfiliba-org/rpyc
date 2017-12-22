import time
import rpyc

c = rpyc.connect("localhost", 18861)

while True:
    start = time.time()
    count = c.root.ping()
    delta = time.time() - start
    print("ping #{} took: {}s".format(count, delta))
