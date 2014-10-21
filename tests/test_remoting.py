import os
import tempfile
import shutil
import unittest
from nose import SkipTest
import rpyc


class Test_Remoting(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.classic.connect_thread()

    def tearDown(self):
        self.conn.close()

    def test_files(self):
        base = tempfile.mkdtemp()
        base1 = os.path.join(base, "1")
        base2 = os.path.join(base, "2")
        base3 = os.path.join(base, "3")
        os.mkdir(base1)
        for i in range(10):
            f = open(os.path.join(base1, "foofoo%d" % (i,)), "w")
            f.close()
        os.mkdir(os.path.join(base1, "somedir1"))

        rpyc.classic.upload(self.conn, base1, base2)
        self.assertEqual(sorted(os.listdir(base1)), sorted(os.listdir(base2)))

        rpyc.classic.download(self.conn, base2, base3)
        self.assertEqual(sorted(os.listdir(base2)), sorted(os.listdir(base3)))

        shutil.rmtree(base)

    def test_distribution(self):
        raise SkipTest("TODO: upload a package and a module")

    def test_interactive(self):
        raise SkipTest("Need to be manually")
        print( "type Ctrl+D to exit (Ctrl+Z on Windows)" )
        rpyc.classic.interact(self.conn)

    def test_post_mortem(self):
        raise SkipTest("Need to be manually")
        try:
            self.conn.modules.sys.path[100000]
        except IndexError:
            print( "type 'q' to exit" )
            rpyc.classic.pm(self.conn)
            raise
        else:
            self.fail("expected an exception")

    def test_migration(self):
        l = rpyc.classic.obtain(self.conn.modules.sys.path)
        self.assertTrue(type(l) is list)
        rl = rpyc.classic.deliver(self.conn, l)
        self.assertTrue(isinstance(rl, rpyc.BaseNetref))


if __name__ == "__main__":
    unittest.main()



