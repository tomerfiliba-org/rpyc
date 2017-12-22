import rpyc
from rpyc.utils.server import ThreadedServer

connections = dict()

class CollectorClientService(rpyc.SlaveService):

    pass

a = ThreadedServer(rpyc.SlaveService, port=4567)
a.start()
