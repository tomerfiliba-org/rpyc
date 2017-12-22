import threading
import rpyc
import rpyc.utils.server

class MyServer(rpyc.Service):
    def exposed_test(self, cb, i):
        def _():
            print "_: calling back", i
            cb(i)
            print "_: called back", i

        th = threading.Thread(target=_)
        th.daemon = True
        th.start()


server = rpyc.utils.server.ThreadedServer(MyServer, port=8888)
server.start()
