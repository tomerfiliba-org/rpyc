import unittest
from rpyc import SlaveService
from rpyc.utils.server import GeventServer
import time
import rpyc
try:
    import gevent
    _gevent_import_failed = False
except Exception:
    _gevent_import_failed = True


@unittest.skipIf(_gevent_import_failed, "Gevent is not available")
class Test_GeventServer(unittest.TestCase):

    def setUp(self):
        from gevent import monkey
        monkey.patch_all()
        self.server = GeventServer(SlaveService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        self.server._listen()
        gevent.spawn(self.server.start)

    def tearDown(self):
        self.server.close()

    def test_connection(self):
        with rpyc.classic.connect("localhost", port=18878) as c:
            c.execute("x = 5")
            self.assertEqual(c.namespace["x"], 5)
            self.assertEqual(c.eval("1+x"), 6)

    def test_multiple_connections(self):
        def get_ident(gevent):
            return gevent.monkey.get_original('threading', 'get_ident')()
        c1 = rpyc.classic.connect("localhost", port=18878)
        c2 = rpyc.classic.connect("localhost", port=18878)
        c3 = rpyc.classic.connect("localhost", port=18878)
        with c1, c2, c3:
            id0 = get_ident(gevent)
            id1 = get_ident(c1.modules.gevent)
            id2 = get_ident(c2.modules.gevent)
            id3 = get_ident(c3.modules.gevent)
            # all server greenlets and clients running in same OS thread ;)
            self.assertEqual(id0, id1)
            self.assertEqual(id1, id2)
            self.assertEqual(id1, id3)

    def test_parallelism(self):
        conns = [rpyc.classic.connect("localhost", port=18878)
                 for _ in range(50)]
        try:
            start = time.time()
            gevent.joinall([
                gevent.spawn(c.modules.time.sleep, 1)
                for c in conns
            ])
            stop = time.time()

            self.assertLessEqual(stop - start, 2)

        finally:
            for c in conns:
                c.close()


if __name__ == "__main__":
    unittest.main()
