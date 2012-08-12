import rpyc
from splitbrain import Splitbrain
import sys

sys.setcheckinterval(1)
conn = rpyc.classic.connect_thread()
sb = Splitbrain(conn)

print "hi"

with sb:
    print "foo"
    import os
    print os, type(os)

print "bye"

import os as os2
print os2, type(os2)

