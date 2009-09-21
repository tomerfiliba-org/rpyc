import os
import rpyc
import time
from subprocess import Popen
from testbase import TestBase
try:
    from rpyc.utils.twisted_integration import RpycClientFactory
    from twisted.internet import reactor
except ImportError:
    reactor = None


class TwistedTest(TestBase):
    PORT = 18814
    
    def setup(self):
        if reactor is None:
            self.cannot_run("requires twisted to be installed")
        fn = os.path.join(os.path.dirname(__file__), "twisted_server.py")
        self.proc = Popen(["python", fn, str(self.PORT)])
        time.sleep(1) # let other process to start first
    
    def cleanup(self):
        self.log("waiting for server process to die")
        self.proc.wait()
    
    def my_client(self, conn):
        self.log("my_client: %s", conn.root.add(17, 3))
        self.require(conn.root.add(30, 2) == 32)
        reactor.callLater(2, self.goodbye, conn)
    
    def my_client2(self, conn):
        self.log("my_client2: %s", conn.root.add(170, 30))
        def cb(x):
            self.log("cb: %s", x)
        conn.root.call(cb)
    
    def goodbye(self, conn):
        self.log("my_client2: %s", conn.root.add(170, 30))
        conn.root.quit()
        reactor.callLater(0, reactor.stop)
    
    def step_main(self):
        reactor.connectTCP("localhost", 18814, RpycClientFactory(rpyc.VoidService, self.my_client))
        reactor.connectTCP("localhost", 18814, RpycClientFactory(rpyc.VoidService, self.my_client2))
        self.log("reactor started")
        reactor.run()


if __name__ == "__main__":
    TwistedTest.run()


