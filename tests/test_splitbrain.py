from __future__ import with_statement
import subprocess
import sys
import os
import time
import signal
import rpyc
import unittest
from rpyc.utils.splitbrain import splitbrain, localbrain


class SplitbrainTest(unittest.TestCase):
    def setUp(self):
        splitbrain.enable()
        server_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "bin", "rpyc_classic.py")
        self.proc = subprocess.Popen([sys.executable, server_file, "-m", "oneshot", "--host=localhost", "-p0"], 
            stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        self.assertEqual(self.proc.stdout.readline().strip(), "rpyc-oneshot")
        host, port = self.proc.stdout.readline().strip().split("\t")
        print (host, port)
        time.sleep(1)
        self.conn = rpyc.classic.connect(host, int(port))
    
    def tearDown(self):
        self.conn.close()
        splitbrain.disable()
    
    def test(self):
        print os.getcwd()
        print type(os)
        with splitbrain(self.conn):
            os.chdir("/")
            print os.getcwd()
        print os.getcwd()
    
    
    


if __name__ == "__main__":
    unittest.main()

