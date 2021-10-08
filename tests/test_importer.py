import subprocess
import sys
import os
import unittest
import importlib

import rpyc


class ImporterTest(unittest.TestCase):
    def setUp(self):
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
        self.proc = subprocess.Popen([sys.executable, server_file, "--mode=oneshot", "--host=localhost", "-p0"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        line = self.proc.stdout.readline().strip()
        if not line:
            print(self.proc.stderr.read())
            self.fail("server failed to start")
        self.assertEqual(line, b"rpyc-oneshot", "server failed to start")
        host, port = self.proc.stdout.readline().strip().split(b"\t")
        self.conn = rpyc.classic.connect(host, int(port))

    def tearDown(self):
        self.conn.close()
        self.proc.communicate()  # clear io so resources are closed

    def test(self):
        # Get the pid of the process running this test
        os = importlib.import_module("os")
        pid = os.getpid()
        # Make RPyC finder first in line for imports
        # sys.meta_path.insert(0, rpyc.utils.importer.RPyCPathFinder(self.conn))
        sys.meta_path.append(rpyc.utils.importer.RPyCPathFinder(self.conn))
        # Trigger re-import from remote
        del sys.modules["os"]
        importlib.invalidate_caches()
        os = importlib.import_module("os")
        importlib.import_module("dffml")
        # Get the pid of the process running the classic server
        remote_pid = os.getpid()
        # Check that remote os module was imported by seeing if the pid changed
        self.assertNotEqual(pid, remote_pid, "Remote os module was not loaded")


if __name__ == "__main__":
    unittest.main()
