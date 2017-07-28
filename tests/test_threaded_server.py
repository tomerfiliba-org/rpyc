import os
import rpyc
import time
import tempfile
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import threading
import unittest


class Test_ThreadedServer(unittest.TestCase):

    def setUp(self):
        self.server = ThreadedServer(SlaveService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.setDaemon(True)
        t.start()
        time.sleep(0.5)

    def tearDown(self):
        self.server.close()

    def test_connection(self):
        c = rpyc.classic.connect("localhost", port=18878)
        print( c.modules.sys )
        print( c.modules["xml.dom.minidom"].parseString("<a/>") )
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()

class Test_ThreadedServerOverUnixSocket(unittest.TestCase):

    def setUp(self):
        self.socket_path = tempfile.mktemp()
        self.server = ThreadedServer(SlaveService, socket_path=self.socket_path, auto_register=False)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.setDaemon(True)
        t.start()
        time.sleep(0.5)

    def tearDown(self):
        self.server.close()
        os.remove(self.socket_path)

    def test_connection(self):
        c = rpyc.classic.unix_connect(self.socket_path)
        print( c.modules.sys )
        print( c.modules["xml.dom.minidom"].parseString("<a/>") )
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()

if __name__ == "__main__":
    unittest.main()
