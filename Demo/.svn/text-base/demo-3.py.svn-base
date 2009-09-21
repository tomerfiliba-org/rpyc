#
# asynchronous proxies as super-events
#
from Rpyc import *

c = SocketConnection("localhost")

#
# this is the remote int type
#
rint = c.modules.__builtin__.int

#
# and we'll wrap it in an asynchronous wrapper
#
rint = Async(rint)

#
# now it still looks like a normal proxy... but operations on it return something called
# an AsyncResult -- it's an object that represents the would-be result of the operation.
# it has a .is_ready property, which indicates whether or not the result is ready, and 
# a .result property, which holds the result of the operations. when you access the .result
# property, it will block until the result is returned
#
a = rint("123")
b = rint("metallica")
print a
print b.is_ready
print a.result
print a

#
# and when an exception occurs, it looks like that
#
try:
    print b.result
except ValueError:
    pass

#
# only when you access the result you get the exception, which may look weird, but hey,
# it's an asynchronous world out there.
#

#
# there's another methodology for async proxies -- on_ready callbacks. instead of 
# getting the async result, you can register a callback to collect it, when it arrives.
#
def f(res):
    print "the result is",
    try:
        print res.result
    except:
        print "an exception"

rint = Async(c.modules.__builtin__.int)

ar = rint("123")
ar.on_ready = f

# this will cause an exception
ar = rint("a perfect circle")
ar.on_ready = f

# or when you dont need to keep the async result 
rint("456").on_ready = f

# and it's not limited to calling it. anything you do to the async proxy is asynchronous.
# for example, you can also get attributes asynchronously:
ar = rint.__str__

#
# now we'll do some other request, which will cause the results to arrive, and the callback 
# to be called. 
#
print c.modules.sys

############################################################################################
#
# this is where we get hardcore: threads and event callbacks
#
xxx = 0
def blah():
    global xxx
    xxx += 1

#
# we'll start a thread on the server which on threadfunc (which is defined in the testmodule).
# this function will call the callback we give it every second, but will ignore the result.
# this practically means it's like an event -- trigger and forget. on the client side, the
# callback will increment `xxx` every time it's called
#
c.modules.thread.start_new_thread(c.modules["Rpyc.Demo.testmodule"].threadfunc, (blah,))

#
# we'll wait a little
#
import time
time.sleep(5)

#
# and do some operation, which, along with it, will pull all incoming requests
#
print c.modules.sys
print xxx

#
# and we can start a thread of our own to pull the requests in the background
#
#import thread
#worker_running = True
#
#def worker(conn):
#    while worker_running:
#        conn.serve()
#
#thread.start_new_thread(worker, (c,))
#
#time.sleep(5)
#worker_running = False
#
#print xxx
#print "goodbye"

#
# L33TN3SS
#


