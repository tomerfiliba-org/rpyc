import rpyc
import time

c = rpyc.classic.connect("localhost")
t = rpyc.BgServingThread(c)

start = time.time()
for i in range(100):
    c.execute("newObj = %d" % (i))
stop = time.time()
print "added %d simple objects one by one, %f seconds" % (100, stop - start)

t.stop()

