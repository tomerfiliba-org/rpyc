import os
import tempfile
import shutil
import unittest
import rpyc


class Test_Remoting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Increase timeout as some of the tests sometimes the
        # command takes longer than 30s, which is the default.
        # This was tested more than 200 times with this value
        # and no problem was visible with this setting.
        cls.sync_request_timeout = rpyc.core.DEFAULT_CONFIG['sync_request_timeout']
        rpyc.core.DEFAULT_CONFIG['sync_request_timeout'] = 60

    @classmethod
    def tearDownClass(cls):
        rpyc.core.DEFAULT_CONFIG['sync_request_timeout'] = cls.sync_request_timeout

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
            f = open(os.path.join(base1, f"foofoo{i}"), "w")
            f.close()
        os.mkdir(os.path.join(base1, "somedir1"))

        rpyc.classic.upload(self.conn, base1, base2)
        self.assertEqual(sorted(os.listdir(base1)), sorted(os.listdir(base2)))

        rpyc.classic.download(self.conn, base2, base3)
        self.assertEqual(sorted(os.listdir(base2)), sorted(os.listdir(base3)))

        shutil.rmtree(base)

    @unittest.skip("TODO: upload a package and a module")
    def test_distribution(self):
        pass

    @unittest.skip("Requires manual testing atm")
    def test_interactive(self):
        print("type Ctrl+D to exit (Ctrl+Z on Windows)")
        rpyc.classic.interact(self.conn)

    @unittest.skip("Requires manual testing atm")
    def test_post_mortem(self):
        try:
            self.conn.modules.sys.path[100000]
        except IndexError:
            print("type 'q' to exit")
            rpyc.classic.pm(self.conn)
            raise
        else:
            self.fail("expected an exception")

    def test_migration(self):
        path_list = rpyc.classic.obtain(self.conn.modules.sys.path)
        self.assertTrue(type(path_list) is list)
        rl = rpyc.classic.deliver(self.conn, path_list)
        self.assertTrue(isinstance(rl, rpyc.BaseNetref))


if __name__ == "__main__":
    unittest.main()
