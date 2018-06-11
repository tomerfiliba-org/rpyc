from __future__ import with_statement
import subprocess
import sys
import os
import rpyc
import unittest
from rpyc.utils.teleportation import export_function, import_function
from rpyc.utils.classic import teleport_function


def b(st):
    if sys.version_info[0] >= 3:
        return bytes(st, "latin-1")
    else:
        return st

def f(a):
    def g(b):
        return a + int(b)
    return g

def h(a):
    import os
    return a * os.getpid()


class TeleportationTest(unittest.TestCase):
    def setUp(self):
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
        self.proc = subprocess.Popen([sys.executable, server_file, "--mode=oneshot", "--host=localhost", "-p0"],
            stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        line = self.proc.stdout.readline().strip()
        if not line:
            print (self.proc.stderr.read())
            self.fail("server failed to start")
        self.assertEqual(line, b("rpyc-oneshot"), "server failed to start")
        host, port = self.proc.stdout.readline().strip().split(b("\t"))
        self.conn = rpyc.classic.connect(host, int(port))

    def tearDown(self):
        self.conn.close()

    def test(self):
        exp = export_function(f)
        f2 = import_function(exp)
        self.assertEqual(f(6)(7), f2(6)(7))

        h2 = teleport_function(self.conn, h)
        self.assertNotEqual(h(7), h2(7))

    def test_globals(self):
        def the_answer():
            return THE_ANSWER

        teleported = teleport_function(self.conn, the_answer)
        self.conn.namespace['THE_ANSWER'] = 42
        self.assertEqual(teleported(), 42)

        the_globals = self.conn.builtins.dict({'THE_ANSWER': 43})
        teleported2 = teleport_function(self.conn, the_answer, the_globals)
        self.assertEqual(teleported2(), 43)


if __name__ == "__main__":
    unittest.main()
