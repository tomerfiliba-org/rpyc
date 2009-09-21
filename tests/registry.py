import time
from testbase import TestBase
from threading import Thread
from rpyc.utils.registry import TCPRegistryServer, TCPRegistryClient
from rpyc.utils.registry import UDPRegistryServer, UDPRegistryClient


PRUNING_TIMEOUT = 5


class BaseRegistryTest(TestBase):
    def _get_server(self):
        raise NotImplementedError
    def _get_client(self):
        raise NotImplementedError
    
    def setup(self):
        self.server = self._get_server()
        self.server.logger.quiet = True
        self.server_thread = Thread(target = self.server.start)
        self.server_thread.setDaemon(True)
        self.server_thread.start()
        time.sleep(0.1)
    
    def cleanup(self):
        self.server.close()
        self.server_thread.join()
    
    def step_api(self):
        c = self._get_client()
        c.logger.quiet = True
        c.register(("FOO",), 12345)
        c.register(("FOO",), 45678)
        res = c.discover("FOO")
        expected = (12345, 45678)
        self.require(set(p for h, p in res) == set(expected))
        c.unregister(12345)
        res = c.discover("FOO")
        expected = (45678,)
        self.require(set(p for h, p in res) == set(expected))
    
    def step_pruning(self):
        c = self._get_client()
        c.logger.quiet = True
        c.register(("BAR",), 17171)

        time.sleep(1)
        res = c.discover("BAR")
        self.require(set(p for h, p in res) == set((17171,)))
        
        time.sleep(PRUNING_TIMEOUT)
        res = c.discover("BAR")
        self.require(res == ())

class TcpRegistryTest(BaseRegistryTest):
    def _get_server(self):
        return TCPRegistryServer(pruning_timeout = PRUNING_TIMEOUT)
    def _get_client(self):
        return TCPRegistryClient("localhost")

class UdpRegistryTest(BaseRegistryTest):
    def _get_server(self):
        return UDPRegistryServer(pruning_timeout = PRUNING_TIMEOUT)
    def _get_client(self):
        return UDPRegistryClient()


if __name__ == "__main__":
    TcpRegistryTest.run()
    UdpRegistryTest.run()

