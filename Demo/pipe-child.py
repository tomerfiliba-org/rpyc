import sys
from Rpyc import PipeConnection

c = PipeConnection(sys.stdin, sys.stdout)
c.modules.sys.path.append("i love lucy")


# child dies