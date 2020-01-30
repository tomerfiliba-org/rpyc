import rpyc
import unittest
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService


# travis: "Network is unreachable", https://travis-ci.org/tomerfiliba/rpyc/jobs/108231239#L450
@unittest.skip("requires IPv6")
class Test_IPv6(unittest.TestCase):
    def setUp(self):
        self.server = ThreadedServer(SlaveService, port=0, ipv6=True)
        self.server.logger.quiet = True
        self.thd = self.server._start_in_thread()

    def tearDown(self):
        self.server.close()
        self.thd.join()

    def test_ipv6_conenction(self):
        c = rpyc.classic.connect("::1", port=self.server.port, ipv6=True)
        print(repr(c))
        print(c.modules.sys)
        print(c.modules["xml.dom.minidom"].parseString("<a/>"))
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()


if __name__ == "__main__":
    unittest.main()
