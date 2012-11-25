import rpyc
import time
import tempfile
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import threading
import unittest

class BaseServerTest(object):

    def _create_server(self):
        raise NotImplementedError

    def _create_client(self):
        raise NotImplementedError

    def setUp(self):
        self.server = self._create_server()
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.setDaemon(True)
        t.start()
        time.sleep(0.5)

    def tearDown(self):
        self.server.close()

    def test_conenction(self):
        c = self._create_client()
        print( c.modules.sys )
        print( c.modules["xml.dom.minidom"].parseString("<a/>") )
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()

class Test_ThreadedServer(BaseServerTest, unittest.TestCase):

    def _create_server(self):
        return ThreadedServer(SlaveService, port=18878, auto_register=False)

    def _create_client(self):
        return rpyc.classic.connect("localhost", port=18878)

class Test_ThreadedServerOverUnixSocket(BaseServerTest, unittest.TestCase):

    socket_path = tempfile.mktemp()

    def _create_server(self):
        return ThreadedServer(SlaveService, socket_path=self.socket_path, auto_register=False)

    def _create_client(self):
        return rpyc.classic.unix_connect(self.socket_path)

if __name__ == "__main__":
    unittest.main()
