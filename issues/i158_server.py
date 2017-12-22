import rpyc
from rpyc.utils.server import ThreadedServer
import rpyc.lib

class MyService(rpyc.Service):
    def exposed_fun(self, id, data):
        print("Exposed fun called with [{}].".format(id))

if __name__ == "__main__":
    rpyc.lib.setup_logger()
    server = ThreadedServer(MyService, port = 12345)
    server.start()
