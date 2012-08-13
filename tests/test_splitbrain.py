import sys
import os
import signal
import time
import subprocess
import rpyc
import unittest
from rpyc.utils.splitbrain import Splitbrain, patch

patch()


class SplitbrainTest(unittest.TestCase):
    def setUp(self):
        server_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "scripts", "rpyc_classic.py")
        self.proc = subprocess.Popen([sys.executable, server_file, "-p", "29992"])
        time.sleep(1)
        self.conn = rpyc.classic.connect("localhost", 29992)
    
    def tearDown(self):
        self.conn.close()
        self.proc.send_signal(signal.SIGINT)
        time.sleep(1)
        self.proc.terminate()
    
    def test_splitbrain(self):
        sb = Splitbrain(self.conn)
        here = os.getcwd()
        self.conn.modules.os.chdir("/")
        
        with sb:
            self.assertEqual(os.getcwd(), "/")
            os.chdir("/etc")
        
        self.assertEqual(os.getcwd(), here)

        with sb:
            self.assertEqual(os.getcwd(), "/etc")

        self.assertEqual(os.getcwd(), here)


if __name__ == "__main__":
    unittest.main()

