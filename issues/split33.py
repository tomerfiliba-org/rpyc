import rpyc
from rpyc.utils.splitbrain import splitbrain, localbrain
import traceback
import sys


c = rpyc.classic.connect("localhost")
import os
pid1 = os.getpid()

with open("tmp.txt", "w") as f:
    f.write("foobar")

with splitbrain(c):
    pid2 = os.getpid()
    assert pid1 != pid2
    import email
    print (email)
    import os as os2
    pid3 = os2.getpid()
    assert pid2 == pid3
    
    assert not os.path.exists("tmp.txt")
    
    with localbrain():
        with open("tmp.txt", "r") as f:
            assert f.read() == "foobar"
        pid4 = os.getpid()
        assert pid4 == pid1
    
    try:
        open("tmp.txt", "r")
    except IOError as ex:
        #print(type(ex), repr(ex))
        with localbrain():
            x = ("".join(traceback.format_exception(*sys.exc_info())))
            print(len(x))
    else:
        assert False, "expected an IOError"

pid5 = os.getpid()
assert pid5 == pid1

print ("done")
