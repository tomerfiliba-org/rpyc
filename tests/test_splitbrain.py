from __future__ import with_statement
import sys
import os
import signal
import time
import subprocess
import rpyc
import unittest
from rpyc.utils.splitbrain import splitbrain, enable, disable


class SplitbrainTest(unittest.TestCase):
    def setUp(self):
        enable()
        #server_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        #    "scripts", "rpyc_classic.py")
        #self.proc = subprocess.Popen([sys.executable, server_file, "-p", "29992"])
        #time.sleep(1)
        #self.conn = rpyc.classic.connect("localhost", 29992)
        self.conn = rpyc.classic.connect("192.168.1.143")
    
    def tearDown(self):
        self.conn.close()
        disable()
        #self.proc.send_signal(signal.SIGINT)
        #time.sleep(1)
        #self.proc.terminate()
    
    def _test_splitbrain(self):
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
    
    def test_splitbrain2(self):
        sb = Splitbrain(self.conn)
        #import shutil
        #from os.path import abspath
        
        with sb:
            from os.path import abspath
            #abspath("")
            #open("test.txt", "w").close()
            #print os.path.exists("test.txt")
            
        print abspath("test.txt")
        
        #print os.path.exists("test.txt")


if __name__ == "__main__":
    unittest.main()

