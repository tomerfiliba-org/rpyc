#
# welcome to RPyC. this demo serves as an introduction. i believe in learning through
# showcases, and that's why this package comes with a demo subpackage, instead of
# documentation
# 
# so, the first thing we're gonna do is import the SocketConnection. this is a factory
# function that returns us a new Connection object over a socket stream. we dont need
# to get into details here.
#
from Rpyc import *

#
# next, we'll get all the helpful utilities. the utilities include wrappers for builtin
# functions, like dir(), so they'd work as expected with netproxies. 
#
from Rpyc.Utils import *

#
# by now you should have an rpyc server running. if you dont, go to the Servers directory
# and choose your favorite version of a socket server. for unixes i'd recommend the 
# forking server; for windows -- the threaded server.
#
# so let's connect to the server
#
c = SocketConnection("localhost")

#
# now it's time to explain a little about how rpyc works. it's quite simple really. the
# magic comes from a concept called NetProxy. a NetProxy object delivers all of the
# operations performed on it to the remote object. so if you get a list from your host,
# what you're are really getting is a NetProxy to that list. it looks and works just
# like a real list -- but everytime you do something on it, it actually performs a 
# request on the list object stored on the host. this is called boxing. this means
# you can change the object you get locally, and the remote object changes, etc.
#
# however, for efficiency and other reason, not all objects you get are NetProxies.
# all immutable and pickle-able objects pass by value (through pickle). these types
# of objects include ints, longs, strings, and some other types. all other types are
# passed by boxing.
#
# this boxing mechanism works on everything -- objects, functions, classes, and modules,
# which is why rpyc is considered transparent. your code looks just as if it was meant 
# to run locally.
#

#
# let's start with something simple -- getting a remote module.  accessing the remote 
# namespace always starts with the `modules` attribute, then the module (or package) 
# name, and then the attribute you want to get.
#

print c.modules.sys
print c.modules.sys.path 
c.modules.sys.path.append("lucy")
print c.modules.sys.path[-1]

#
# these remote objects are first class objects, like all others in python. this means
# you can store them in variables, pass them as parameters, etc.
#
rsys = c.modules.sys
rpath = rsys.path
rpath.pop(-1)

#
# and as you might expect, netproxies also look like the real objects
#
print dir(rpath)

#
# but there are a couple of issues with netproxies. the type(), isinstance(), and 
# issubclass() classes dont work on them... as they query the underlying object, not
# the remote one. so:
#
print type(rsys.maxint) # <int> -- because it's a simple type which is passed by value)
print type(rsys.path)   # <SyncNetProxy> -- because, after all, it's a netproxy, not a list

#
# now for a demo of packages
# (which looks very much like 'from xml.dom.minidom import parseString')
#
parseString = c.modules.xml.dom.minidom.parseString
x = parseString("<a>lala</a>")
print x
x.toxml()
print x.firstChild.nodeName

#
# however, there's a catch when working with packages like that. the way it works is
# trying to find an attribute with that name, and if not found, trying to import a sub-
# module. 
#
# now in english:
# c.module.xml is the xml module of the server. when you do c.module.xml.dom, rpyc looks
# for an attribute named 'dom' inside the xml module. since there's no such attribute,
# it tries to import a subpackage called xml.dom, which succeeds. then it does the same
# for xml.dom.minidom, and xml.dom.minidom.parseString.
#
# but there are times when that's ambiguous. this mean that the module has both a sub-
# module called 'X', and an attribute called 'X'. according to rpyc's algorithm, the
# attribute 'X' is returned, not the sub-module.
#
# but if you need to be explicit, you can, and it works like this:
#

c.modules["xml.dom.minidom"].parseString("<a></a>")

#
# this will make sure the module 'xml.dom.minidom' is returned, and not an attribute.
# in general, it's better to use this form, unless you know there are no such conflicts.
# remeber that "Explicit is better than implicit", although it requires four more key
# strokes. perhaps in a later version it will raise an exception if there's a conflict.
#

#
# and now for a little demo of working with files (a common task)
#
f = c.modules.__builtin__.open("lala.txt", "w")
f.write("lucy")
f.close()
c.modules.os.remove("lala.txt")

#
# now to a bitter part of life: exceptions. as you could expect, they work just like
# regular exceptions
#
try:
    a = c.modules.sys.nonexistent_attribute
except AttributeError:
    pass
else:
    assert False

try:
    a = c.modules.__builtin__.open("**\\//##~~..::!@#$%^&*()_+\n <,>?")
except IOError:
    pass
else:
    assert False

print "goodbye"















