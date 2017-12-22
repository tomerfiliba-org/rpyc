import rpyc

from rpyc.utils.server import ThreadedServer

class service(rpyc.Service):
    def exposed_func(self):
        print("Hi!")

server = ThreadedServer(service, hostname='localhost', port=4158)
server.start()
