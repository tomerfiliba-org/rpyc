import time

from threading import Thread
from rpyc.utils.registry import TCPRegistryServer, TCPRegistryClient
from rpyc.utils.registry import UDPRegistryServer, UDPRegistryClient


PRUNING_TIMEOUT = 5


class BaseRegistryTest(object):
    def _get_server(self):
        raise NotImplementedError

    def _get_client(self):
        raise NotImplementedError
    
    def setup(self):
        self.server = self._get_server()
        self.server.logger.quiet = True
        self.server_thread = Thread(target=self.server.start)
        self.server_thread.setDaemon(True)
        self.server_thread.start()
        time.sleep(0.1)
    
    def teardown(self):
        self.server.close()
        self.server_thread.join()
    
    def test_api(self):
        c = self._get_client()
        c.logger.quiet = True
        c.register(("FOO",), 12345)
        c.register(("FOO",), 45678)
        res = c.discover("FOO")
        expected = (12345, 45678)
        assert set(p for h, p in res) == set(expected)
        c.unregister(12345)
        res = c.discover("FOO")
        expected = (45678,)
        assert set(p for h, p in res) == set(expected)
    
    def test_pruning(self):
        c = self._get_client()
        c.logger.quiet = True
        c.register(("BAR",), 17171)

        time.sleep(1)
        res = c.discover("BAR")
        assert set(p for h, p in res) == set((17171,))
        
        time.sleep(PRUNING_TIMEOUT)
        res = c.discover("BAR")
        assert res == ()


class Test_TcpRegistry(BaseRegistryTest):
    def _get_server(self):
        return TCPRegistryServer(pruning_timeout=PRUNING_TIMEOUT)

    def _get_client(self):
        return TCPRegistryClient("localhost")

class Test_UdpRegistry(BaseRegistryTest):
    def _get_server(self):
        return UDPRegistryServer(pruning_timeout=PRUNING_TIMEOUT)

    def _get_client(self):
        return UDPRegistryClient()
