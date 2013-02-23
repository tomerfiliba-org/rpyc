from __future__ import with_statement
import subprocess
import sys
import os
import rpyc
import six
import unittest
import tempfile
import shutil
import traceback
from rpyc.utils.splitbrain import splitbrain, localbrain


if not hasattr(unittest.TestCase, "assertIn"):
    unittest.TestCase.assertIn = lambda self, member, container, msg = None: self.assertTrue(member in container, msg)
if not hasattr(unittest.TestCase, "assertNotIn"):
    unittest.TestCase.assertNotIn = lambda self, member, container, msg = None: self.assertFalse(member in container, msg)

from nose import SkipTest
if sys.version_info >= (3, 3):
    raise SkipTest("Python 3.3 doesn't work right now")


class SplitbrainTest(unittest.TestCase):
    def setUp(self):
        splitbrain.enable()
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
        self.proc = subprocess.Popen([sys.executable, server_file, "--mode=oneshot", "--host=localhost", "-p0"], 
            stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        self.assertEqual(self.proc.stdout.readline().strip(), six.b("rpyc-oneshot"))
        host, port = self.proc.stdout.readline().strip().split(six.b("\t"))
        self.conn = rpyc.classic.connect(host, int(port))
    
    def tearDown(self):
        self.conn.close()
        splitbrain.disable()
    
    def test(self):
        here = os.getcwd()
        mypid = os.getpid()
        with open("split-test.txt", "w") as f:
            f.write("foobar")
        
        with splitbrain(self.conn):
            try:
                path = tempfile.mkdtemp()
                
                import email
                
                self.assertNotIn("stale", repr(email))
                
                os.chdir(path)
                hispid = os.getpid()
                self.assertNotEqual(mypid, hispid)
                here2 = os.getcwd()
                self.assertNotEqual(here, here2)
                self.assertFalse(os.path.exists("split-test.txt"))
                with open("split-test.txt", "w") as f:
                    f.write("spam")
                
                with localbrain():
                    self.assertEqual(os.getpid(), mypid)
                    with open("split-test.txt", "r") as f:
                        self.assertEqual(f.read(), "foobar")
                
                try:
                    def f():
                        g()
                    def g():
                        h()
                    def h():
                        open("crap.txt", "r")
                    f()
                except IOError:
                    tbtext = "".join(traceback.format_exception(*sys.exc_info()))
                    #pdb.post_mortem(sys.exc_info()[2])
                    self.assertIn("f()", tbtext)
                    self.assertIn("g()", tbtext)
                    self.assertIn("h()", tbtext)
                else:
                    self.fail("This should have raised a IOError")

            finally:
                # we must move away from the tempdir to delete it (at least on windows)
                os.chdir("/")
                shutil.rmtree(path)
        
        self.assertIn("stale", repr(email))
        
        self.assertEqual(os.getpid(), mypid)
        self.assertEqual(os.getcwd(), here)
        
        os.remove("split-test.txt")
    
    


if __name__ == "__main__":
    unittest.main()

