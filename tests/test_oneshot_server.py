import rpyc
from rpyc.utils.server import OneShotServer
import unittest


class MyService(rpyc.Service):

    def exposed_foo(self):
        return "bar"


class Test_OneShotServer(unittest.TestCase):

    def setUp(self):
        self.server = OneShotServer(MyService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        self.thd = self.server._start_in_thread()

    def tearDown(self):
        self.server.close()
        self.thd.join()

    def test_server_stops(self):
        conn = rpyc.connect("localhost", port=18878)
        self.assertEqual("bar", conn.root.foo())
        conn.close()
        while not self.server._closed:
            pass
        self.assertTrue(self.server._closed)
        with self.assertRaises(Exception):
            conn = rpyc.connect("localhost", port=18878)


if __name__ == "__main__":
    unittest.main()
