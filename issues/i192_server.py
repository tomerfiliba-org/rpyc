import rpyc
from rpyc.utils.server import ThreadedServer
import rpyc.lib

class SomeService(rpyc.Service):
    def exposed_use_list(self, lst):
        return lst + [4, 5, 6]


if __name__ == "__main__":
    rpyc.lib.setup_logger()
    server = ThreadedServer(SomeService, port = 12345)
    server.start()
