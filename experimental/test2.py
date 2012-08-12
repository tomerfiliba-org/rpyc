import rpyc
from splitbrain import Splitbrain
import sys

sys.setcheckinterval(1)
conn = rpyc.classic.connect("localhost")
sb = Splitbrain(conn)

print "hi"

with sb:
    print "foo"
    import os
    import sys as sys2
    import xml.dom.minidom
    print xml.dom.minidom
    print os, type(os)

print "out"

import os as os2
print os2, type(os2)

print os is os2

print "bye"
