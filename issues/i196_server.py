import rpyc
from rpyc.utils.server import ThreadedServer
import rpyc.lib



class X(object):
    def __init__(self):
        self.exposed_remote_attr = ['foo']


class MyService(rpyc.Service):
    exposed_remote_object = X()

    def exposed_get(self):
        return self._conn._local_objects._dict



if __name__ == "__main__":
    rpyc.lib.setup_logger()
    server = ThreadedServer(MyService, port = 12345)
    server.start()
