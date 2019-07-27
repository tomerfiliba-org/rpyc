import time
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
        self.server._start_in_thread()

    def tearDown(self):
        self.server.close()

    def test_server_stops(self):
        conn = rpyc.connect("localhost", port=18878)
        self.assertEqual("bar", conn.root.foo())
        conn.close()
        with self.assertRaises(Exception):
            for i in range(3):
                conn = rpyc.connect("localhost", port=18878)
                conn.close()
                time.sleep()


if __name__ == "__main__":
    unittest.main()
