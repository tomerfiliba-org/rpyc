# a demo for parent/child over pipes

import sys
from popen2 import popen3
from Rpyc import PipeConnection

cout, cin, cerr = popen3("python pipe-child.py")
conn = PipeConnection(cout, cin)

try:
    while True:
        conn.serve()
except EOFError:
    print "goodbye child"

print sys.path[-1]

