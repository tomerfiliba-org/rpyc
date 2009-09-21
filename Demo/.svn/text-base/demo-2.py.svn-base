#
# okay, this demo is more advanced. here we'll learn about:
#  * redirecting standard files
#  * synchronous callbacks
#  * the ulitities module
#
import sys
import os 
from Rpyc import *
from Rpyc.Utils import remote_interpreter

c = SocketConnection("localhost")

#
# redirect our stdout to the server
#
sys.stdout = c.modules.sys.stdout
print "this time we focus on `the seatle music`"

#
# and the other way round
#
sys.stdout = sys.__stdout__
c.modules.sys.stdout = sys.stdout
c.modules.sys.stdout.write("alice in chains\n")

#
# but you dont believe me, so 
#
c.modules["Rpyc.Demo.testmodule"].printer("tool")

#
# and restore that
#
c.modules.sys.stdout = c.modules.sys.__stdout__

#
# now let's play with callbacks
#
def f(text):
    print text

c.modules["Rpyc.Demo.testmodule"].caller(f, "nirvana")

#
# and if you insist
#
def g(func, text):
    c.modules["Rpyc.Demo.testmodule"].caller(func, text)

c.modules["Rpyc.Demo.testmodule"].caller(g, f, "soundgarden")

#
# now for the utilities module. it gives us the following cool functions:
#  * dir, getattr, hasattr, help, reload -- overriding builtins 
#  * upload, download -- transfering files/directories to/from the client/server (all the permutations)
#  * remote_shell, remote_interpreter -- running remote processess and debugging
#
print hasattr(sys, "path")
print hasattr(c.modules.sys, "path")

print getattr(sys, "maxint")
print getattr(c.modules.sys, "maxint")

print reload(sys)
print reload(c.modules.sys)

f=open("lala.txt", "w")
f.write("king crimson")
f.close()
upload(c, "lala.txt", "../lala.txt")
os.remove("lala.txt")
c.modules.os.remove("../lala.txt")

remote_interpreter(c)


print "goodbye"



