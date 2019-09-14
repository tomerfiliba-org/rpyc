import rpyc
from rpyc.utils.server import ThreadedServer
import unittest


class Foo:

    def __str__(self):
        return "Foo"


class Service(rpyc.Service):

    PORT = 18878

    def exposed_foo(self, arg):
        return str(arg)

class Intermediate(rpyc.Service):

    PORT = 18879

    def exposed_foo(self, arg):
        with rpyc.connect("localhost", port=Service.PORT) as conn:
            return conn.root.foo(arg)

class Test_rpyc_over_rpyc(unittest.TestCase):
    """Issue #346 shows that exceptions are being raised when an RPyC service method
    calls another RPyC service, forwarding a non-trivial (and thus given as a proxy) argument.
    """

    def setUp(self):
        self.server = ThreadedServer(Service, port=Service.PORT, auto_register=False)
        self.i_server = ThreadedServer(Intermediate, port=Intermediate.PORT, auto_register=False)
        self.server._start_in_thread()
        self.i_server._start_in_thread()
        self.conn = rpyc.connect("localhost", port=Intermediate.PORT)

    def tearDown(self):
        self.conn.close()
        self.server.close()
        self.i_server.close()

    def test_rpyc_over_rpyc(self):
        """Tests using rpyc over rpyc throws an exception as described in #346"""
        obj = Foo()
        result = self.conn.root.foo(obj)
        self.assertEqual(result, str(obj))


if __name__ == "__main__":
    unittest.main()
