# as you can see - the import line now requires even less typing!
from Rpyc import *
c = SocketConnection("localhost")

#------------------------------------------------------------------------------ 
# this demo shows the new `execute` and `namespace` features of rpyc
#------------------------------------------------------------------------------ 


# the code below will run AT THE OTHER SIDE OF THE CONNECTION... so you'll see
# 'hello world' on the server's console
c.execute("print 'hello world'")

import sys
c.modules.sys.stdout = sys.stdout

# and this time, on our console
c.execute("print 'brave new world'")

# restore that
c.modules.sys.stdout = c.modules.sys.__stdout__

# anyway, the `execute` method runs the given code at the other side of the connection
# and works in the `namespace` dict. what?
c.execute("x = [1,2,3]")
print c.namespace.x

# now it makes sense, doesn't it? the 'namespace' attribute is something i called 
# AttrFrontend -- it wraps a dict with the attribute protocol, so you can access
# it with the dot notation, instead of the braces notation (more intuitive).
# this namespace works both ways -- executing code affects the namespace, while
# altering the namespace directly also affects it:
c.namespace.x.append(4)
c.execute("x.append(5)")
print c.namespace.x

# but you should not assign complex objects (not int/float/str, etc) to this namespace
# directy, or NetProxies will be created. there's nothing wrong with that, but keep
# in mind it might cause blocking (and even deadlocks), as i'll explain later.

# another cool thing i want to show is the second, optional parameter to execute: mode.
# the mode controls how the code is compiled. the default mode is "exec", which means 
# it executes the code as a module. the other option is "eval" which returns a value.
# so if you want to _do_ something, like printing of assigning a variable, you do it 
# with "exec", and if you want to evaluate something, you do it with "eval"
# for example:

# this will print None
print c.execute("1+2")

# while this will print 3
print c.execute("1+2", "eval")

# but there's a time in a man's life when he asks himself, why the heck? you can, as i 
# showed in other places, just do this:
#     c.modules.__builtin__.eval("1+2")
# so what's the point? 
#
# well, i've been waiting for this question. the rationale behind this seemingly useless 
# feature is for times you NEED to have the code executing remotely, but writing a 
# dedicated module for it is overdoing it:
#  * more files to update ==> more chance that you'll forget to update
#  * distributing the module to all of the machines
#  * making a mess on the file system
#  * it's really not a module... it's just some code that logically belongs to one single 
#    module, but technical difficulties prevent it
#
# and to show you what i mean -- i want to start a thread on the server, like it did in 
# several places over the demos. this thread will send me an event every second. what i 
# used to do was, creating another module, like testmodule.py to define the thread 
# function, so it will exist on the server, and i could call it.
# if i defined thread_func at the client side, then the thread will block when trying 
# to execute the code, because the client holds it. so this new mechanism lets you 
# distribute code in a volatile fashion:
#  * when the connection is closed, everything you defined is gone
#  * no file-system mess
#  * no need to distribute files across the network
#  * only one place to maintain

c.execute("""
my_thread_active = True

def my_thread_func(callback):
    import time
    from Rpyc import Async

    callback = Async(callback)
    while my_thread_active:
        callback(time.time())
        time.sleep(1)
    print "the thread says goodbye"
""")

def callback(timestamp):
    print "the timestamp is", timestamp

c.modules.thread.start_new_thread(c.namespace.my_thread_func, (callback,))
c.modules.time.sleep(5)
c.namespace.my_thread_active = False
c.close()

# it's not only for threads of course. there are many times when you NEED the code/objects 
# on the remote side. for example:
#  * situations that would block (like having the thread func on the client)
#  * code that check the type of the object (type or isinstance), and a NetProxy would make
#    it cry. DONT CHECK THE TYPE OF OBJECTS, PEOPLE, JUST USE THEM! that's why they invented 
#    duck-typing. argh.
#  * other places i didnt think of as of yet. i want to sleep. leave me alone ;) zzzZZZ
#
# so enjoy!




















