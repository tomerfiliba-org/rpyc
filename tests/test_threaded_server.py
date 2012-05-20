import rpyc
import time
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import threading
import unittest


class Test_ThreadedServer(unittest.TestCase):
    def setUp(self):
        self.server = ThreadedServer(SlaveService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        time.sleep(0.5)

    def tearDown(self):
        self.server.close()

    def test_conenction(self):
        c = rpyc.classic.connect("localhost", port=18878)
        print( c.modules.sys )
        print( c.modules["xml.dom.minidom"].parseString("<a/>") )
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()


if __name__ == "__main__":
    unittest.main()
