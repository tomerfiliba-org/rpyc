import os
import sys
import unittest
import subprocess
import importlib.util
import time
import rpyc
_gevent_spec = importlib.util.find_spec("gevent")
_gevent_missing = _gevent_spec is None

@unittest.skipIf(_gevent_missing, "Gevent is not available")
class Test_GeventServer(unittest.TestCase):

    def setUp(self):
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gevent_service.py")
        self.proc = subprocess.Popen([sys.executable, '-u', server_file],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.ident = int(self.proc.stdout.readline().strip())
        if not self.ident:
            print(self.proc.stderr.read())
            self.fail("server failed to start")

    def tearDown(self):
        self.proc.terminate()
        self.proc.communicate()  # clear io so resources are closed
        self.proc.wait()

    def test_connection(self):
        with rpyc.classic.connect("localhost", port=18878) as c:
            c.execute("x = 5")
            self.assertEqual(c.namespace["x"], 5)
            self.assertEqual(c.eval("1+x"), 6)

    def test_multiple_connections(self):
        c1 = rpyc.classic.connect("localhost", port=18878)
        c2 = rpyc.classic.connect("localhost", port=18878)
        c3 = rpyc.classic.connect("localhost", port=18878)
        with c1, c2, c3:
            id1 = c1.root.get_ident()
            id2 = c2.root.get_ident()
            id3 = c2.root.get_ident()
            # all server greenlets and clients running in same OS thread ;)
            self.assertEqual(id1, self.ident)
            self.assertEqual(id1, id2)
            self.assertEqual(id1, id3)

    def test_parallelism(self):
        conns = [rpyc.classic.connect("localhost", port=18878)
                 for _ in range(50)]
        try:
            start = time.time()
            for t in [
                rpyc.worker(c.modules.time.sleep, 1)
                for c in conns
            ]:
                t.join()
            stop = time.time()

            self.assertLessEqual(stop - start, 2)

        finally:
            for c in conns:
                c.close()


if __name__ == "__main__":
    unittest.main()
