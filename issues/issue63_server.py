import threading
import rpyc


def run_something(callback):
    for i in range(100):
        callback(i)

class MyService(rpyc.Service):
    def on_connect(self):
        print "hi", self._conn._config["endpoints"][1]
    def on_disconnect(self):
        print "bye", self._conn._config["endpoints"][1]
    
    class exposed_RemoteCallbackTest(object):
        def __init__(self, callback):
            self.callback = callback
        def start(self):
            thd = threading.Thread(target = run_something, args = (self.callback,))
            thd.start()


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    myServerObj = ThreadedServer(MyService, port=12000, protocol_config={"allow_public_attrs":True})
    myServerObj.start()

