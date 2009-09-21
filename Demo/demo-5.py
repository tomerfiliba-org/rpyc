#
# this demo will show you working with asynch proxies and callback
# verison 2.3 removes the AsyncCallback factory, and instead provides a mechanism
# where async results can provide a callback. it simplifies the design, so i
# went for it.
#
import time
from Rpyc import SocketConnection, Async

c1 = SocketConnection("localhost")

# f1 is an async proxy to the server's sleep function
f1 = Async(c1.modules.time.sleep)

# this would block the server for 9 seconds
r1 = f1(9)
# and this would block it for 11
r2 = f1(11)

# of course the client isnt affected (that's the whole point of Async)
# but since the same server can't block simultaneously, the second request is
# queued. this is a good example of queuing.

# now we'll wait for both results to finish. this should print around 20 lines
# (more or less, depending on the phase)
while not r1.is_ready or not r2.is_ready:
    print "!"
    time.sleep(1)

print "---"

# now we'll dig in the h4xx0r shit -- running things simultaneously
# for this, we'll need another connection, and another proxy:
c2 = SocketConnection("localhost")
f2 = Async(c2.modules.time.sleep)

# now we'll do the same as the above, but this time, it will happen simulatenously
# becuase f1 and f2 work on different connections
r1 = f1(9)
r2 = f2(11)

# so this time, it will print around 11 lines
while not r1.is_ready or not r2.is_ready:
    print "!"
    time.sleep(1)

print "---"

# very haxxor indeed. now, we'll see how to use the on_ready callback
r1 = f1(9)
r2 = f2(11)

def blah(res):
    print "look mama, no hands! res = %r" % (res.result,)

# set the on_ready callback -- when r1 is becomes ready, the callback will
# be called automagically
r1.on_ready = blah 

# this should print 9 "!", then "look mama", then two more "!"
while not r1.is_ready or not r2.is_ready:
    print "!"
    time.sleep(1)



