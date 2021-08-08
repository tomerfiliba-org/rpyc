import time
import unittest

import rpyc
from rpyc.utils.registry import TCPRegistryServer, TCPRegistryClient
from rpyc.utils.registry import UDPRegistryServer, UDPRegistryClient


PRUNING_TIMEOUT = 5


class BaseRegistryTest(object):
    def _get_server(self):
        raise NotImplementedError

    def _get_client(self):
        raise NotImplementedError

    def setUp(self):
        self.server = self._get_server()
        self.server.logger.quiet = True
        self.server_thread = rpyc.spawn(self.server.start)

    def tearDown(self):
        self.server.close()
        self.server_thread.join()

    def test_api(self):
        c = self._get_client()
        c.logger.quiet = True
        c.register(("FOO",), 12345)
        c.register(("FOO",), 45678)
        res = c.discover("FOO")
        expected = (12345, 45678)
        self.assertEqual(set(p for _, p in res), set(expected))
        c.unregister(12345)
        res = c.discover("FOO")
        expected = (45678,)
        self.assertEqual(set(p for _, p in res), set(expected))
        res = c.list()
        expected = ("FOO",)
        self.assertEqual(set(p for p in res), set(expected))
        c.register(("BAR",), 54321)
        res = c.list()
        expected = ("FOO", "BAR")
        self.assertEqual(set(res), set(expected))

    def test_pruning(self):
        c = self._get_client()
        c.logger.quiet = True
        c.register(("BAR",), 17171)

        time.sleep(1)
        res = c.discover("BAR")
        self.assertEqual(set(p for _, p in res), set((17171,)))

        time.sleep(PRUNING_TIMEOUT)
        res = c.discover("BAR")
        self.assertEqual(res, ())


class TestTcpRegistry(BaseRegistryTest, unittest.TestCase):
    def _get_server(self):
        return TCPRegistryServer(pruning_timeout=PRUNING_TIMEOUT, allow_listing=True)

    def _get_client(self):
        return TCPRegistryClient("localhost")


class TestUdpRegistry(BaseRegistryTest, unittest.TestCase):
    def _get_server(self):
        return UDPRegistryServer(pruning_timeout=PRUNING_TIMEOUT, allow_listing=True)

    def _get_client(self):
        return UDPRegistryClient()


if __name__ == "__main__":
    unittest.main()
