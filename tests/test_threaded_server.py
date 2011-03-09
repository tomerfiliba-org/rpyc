import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import threading

class Test_ThreadedServer(object):
    def setup(self):
        self.server = ThreadedServer(SlaveService, 
            hostname = "localhost", port=18874, auto_register=False)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        
    def teardown(self):
        self.server.close()
        
    def test_conenction(self):
        c = rpyc.classic.connect("localhost", port=18874)
        print c.modules.sys
        print c.modules["xml.dom.minidom"].parseString("<a/>")
        c.execute("x = 5")
        assert c.namespace["x"] == 5
        assert c.eval("1+x") == 6
        c.close()