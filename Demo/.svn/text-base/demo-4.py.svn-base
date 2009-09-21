import time
from Rpyc import SocketConnection, Async

c = SocketConnection("localhost")
c2 = SocketConnection("localhost")

huge_xml = "<blah a='5' b='6'>   " * 50000 + "   </blah> " * 50000
parseString = Async(c.modules.xml.dom.minidom.parseString)
res = parseString(huge_xml)

print "while we're waiting for the server to complete, we do other stuff"
t = time.time()
while not res.is_ready:
    time.sleep(0.5)
    # we dont want to use `c`, because it would block us (as the server is blocking)
    # but `c2` runs on another thread/process, so it wouldn't block
    print c2.modules.os.getpid()

t = time.time() - t
print "it took %d seconds" % (t,)

print res.result


#
# note: to improve performance, delete the result when you no longer need it.
# this should be done because the server might (as in this case) hold enormous 
# amounts of memory, which will slow it down
#
# if you do this:
#   res = parseString(huge_xml)
#   res = parseString(huge_xml)
# res will be deleted only after the second operation finishes, because only when
# the second result is assigned, the first is released -- server still holds 
# around 160MB of the old xml tree for nothing. so it's a good idea to `del res` 
# when you dont need it.
#
# also, there's a memory leak on the server, which i'm working on solving.
#


