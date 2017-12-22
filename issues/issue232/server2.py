
import rpyc
from rpyc.core.service import ModuleNamespace
from rpyc.utils.server import ThreadedServer

class MasterService(rpyc.VoidService):

    def on_connect(self):
        conn = self._conn
        # initialize SlaveService peer:
        conn.modules = ModuleNamespace(self._conn.root.getmodule)
        conn.eval = self._conn.root.eval
        conn.execute = self._conn.root.execute
        conn.namespace = self._conn.root.namespace

        # control client
        print(conn.modules.os.getcwd())
        conn.close()


server = ThreadedServer(MasterService, port=4567)
server.start()
