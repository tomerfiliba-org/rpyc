import rpyc
from rpyc.core.service import ModuleNamespace
import time

conn = rpyc.connect("localhost", port=4567, service=rpyc.VoidService)
modules = ModuleNamespace(conn.root.getmodule)

#conn = rpyc.classic.connect("localhost", port=4567)
print(modules.sys.argv) # throws here exception


#while True:
#    time.sleep(1)
