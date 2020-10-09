import os
import rpyc
import tempfile
from rpyc.utils.server import ThreadedServer, ThreadPoolServer
from rpyc import SlaveService
import unittest


class Test_ThreadedServer(unittest.TestCase):

    def setUp(self):
        self.server = ThreadedServer(SlaveService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        self.server._start_in_thread()

    def tearDown(self):
        while self.server.clients:
            pass
        self.server.close()

    def test_connection(self):
        conn = rpyc.classic.connect("localhost", port=18878)
        print(conn.modules.sys)
        print(conn.modules["xml.dom.minidom"].parseString("<a/>"))
        conn.execute("x = 5")
        self.assertEqual(conn.namespace["x"], 5)
        self.assertEqual(conn.eval("1+x"), 6)
        conn.close()


class Test_ThreadedServerOverUnixSocket(unittest.TestCase):

    def setUp(self):
        self.socket_path = tempfile.mktemp()
        self.server = ThreadedServer(SlaveService, socket_path=self.socket_path, auto_register=False)
        self.server.logger.quiet = False
        self.server._start_in_thread()

    def tearDown(self):
        self.server.close()
        os.remove(self.socket_path)

    def test_connection(self):
        c = rpyc.classic.unix_connect(self.socket_path)
        print(c.modules.sys)
        print(c.modules["xml.dom.minidom"].parseString("<a/>"))
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()


class Test_ThreadPoolServer(Test_ThreadedServer):

    def setUp(self):
        self.server = ThreadPoolServer(SlaveService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        self.server._start_in_thread()


if __name__ == "__main__":
    unittest.main()
