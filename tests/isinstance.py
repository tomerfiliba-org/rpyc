from Rpyc import *
import time
c=SocketConnection("localhost")

t=time.time()
assert isinstance(1, int) == True
assert isinstance(1, float) == False
assert isinstance(1, (int, float)) == True
assert isinstance(1, (str, float)) == False

assert isinstance(c.modules.sys.path, list) == True
assert isinstance(c.modules.sys.path, str) == False
assert isinstance(c.modules.sys.path, (list, str)) == True
assert isinstance(c.modules.sys.path, (int, str)) == False

assert isinstance(c.modules.sys.path, c.modules.__builtin__.list) == True
assert isinstance(c.modules.sys.path, (str, c.modules.__builtin__.list)) == True
assert isinstance(c.modules.sys.path, c.modules.__builtin__.int) == False
assert isinstance(c.modules.sys.path, (str, c.modules.__builtin__.int)) == False

assert isinstance([1,2,3], c.modules.__builtin__.list) == True
assert isinstance([1,2,3], c.modules.__builtin__.int) == False
assert isinstance([1,2,3], (c.modules.__builtin__.list, int)) == True
assert isinstance([1,2,3], (c.modules.__builtin__.int, int)) == False

assert issubclass(str, str) == True
assert issubclass(str, basestring) == True
assert issubclass(str, (int, basestring)) == True
assert issubclass(str, int) == False
assert issubclass(str, (int, float)) == False

assert issubclass(c.modules.__builtin__.str, str) == True
assert issubclass(c.modules.__builtin__.str, basestring) == True
assert issubclass(c.modules.__builtin__.str, (list, basestring)) == True
assert issubclass(c.modules.__builtin__.str, int) == False
assert issubclass(c.modules.__builtin__.str, (int, float)) == False

assert issubclass(c.modules.__builtin__.str, c.modules.__builtin__.str) == True
assert issubclass(c.modules.__builtin__.str, c.modules.__builtin__.basestring) == True
assert issubclass(c.modules.__builtin__.str, (list, c.modules.__builtin__.basestring)) == True
assert issubclass(c.modules.__builtin__.str, c.modules.__builtin__.int) == False
assert issubclass(c.modules.__builtin__.str, (c.modules.__builtin__.int, c.modules.__builtin__.float)) == False

assert issubclass(str, c.modules.__builtin__.str) == True
assert issubclass(str, c.modules.__builtin__.basestring) == True
assert issubclass(str, (int, c.modules.__builtin__.basestring)) == True
assert issubclass(int, c.modules.__builtin__.str) == False
assert issubclass(int, (c.modules.__builtin__.str, float)) == False

t=time.time()-t
print "all okay", t


