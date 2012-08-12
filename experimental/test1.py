#from __future__ import print_function
import pyximport; pyximport.install()
from subinterpreter import SubInterpreter


print ("hello")

import sys
sys.setcheckinterval(0)

subint = SubInterpreter()
subint2 = SubInterpreter()

with subint:
    for i in range(2):
        print ("foo")
        print ("bar")
    print "zzzzz"
    import sys as sys2
    #import xml.dom.minidom
    print (sys is sys2)
    for i in range(2):
        print ("foo")
        print ("bar")

print "lala"

try:
    with subint2:
        import sys as sys3
        print (sys is sys3)
        print (sys is sys2)
        print (sorted(sys3.modules.keys()))
        1/0
except ZeroDivisionError as ex:
    print ex

with subint:
    print (sorted(sys2.modules.keys()))

print ("outta here")
 
subint.close()
subint2.close()

print ("bye")

