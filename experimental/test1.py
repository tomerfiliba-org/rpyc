#from __future__ import print_function
import pyximport; pyximport.install()
import __builtin__
from subinterpreter import SubInterpreter


print "hello"

import sys
sys.setcheckinterval(0)

subint = SubInterpreter()
subint2 = SubInterpreter()

def f():
    g()

def g():
    h()

def h():
    import sys as sys2
    print "restricted = ", sys2._getframe().f_restricted

with subint:
    print "foo"
    print "bar"
    import __builtin__ as builtin2
    import sys as sys2

    print "restricted = ", sys2._getframe().f_restricted
    
    f()
    
    print "builtin:", __builtin__ is builtin2
    print sys is sys2
    import xml.dom.minidom
    print "spam"
    print "bacon"

print "lala"

try:
    with subint2:
        import sys as sys3
        print sys is sys3
        print sys is sys2
        print sorted(sys3.modules.keys())
        1/0
except ZeroDivisionError as ex:
    print ex

with subint:
    print sorted(sys2.modules.keys())

print "outta here"

