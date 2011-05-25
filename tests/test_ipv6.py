import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import threading
import socket

from nose import SkipTest

if not getattr(socket, "has_ipv6", False):
    raise SkipTest("requires IPv6")


class Test_IPv6(object):
    def setup(self):
        self.server = ThreadedServer(SlaveService, port = 0, ipv6 = True)
        self.server.logger.quiet = True
        self.thd = threading.Thread(target = self.server.start)
        self.thd.start()

    def teardown(self):
        self.server.close()
        self.thd.join()

    def test_ipv6_conenction(self):
        c = rpyc.classic.connect("::1", port = self.server.port, ipv6 = True)
        print( repr(c) )
        print( c.modules.sys )
        print( c.modules["xml.dom.minidom"].parseString("<a/>") )
        c.execute("x = 5")
        assert c.namespace["x"] == 5
        assert c.eval("1+x") == 6
        c.close()

