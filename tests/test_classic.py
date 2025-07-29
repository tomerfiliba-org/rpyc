import os
import sys
import rpyc
import unittest
from subprocess import PIPE
from rpyc.core.consts import STREAM_CHUNK


def splice_to_stderr(stream):
    try:
        while True:
            data = stream.read(STREAM_CHUNK)
            if not data:
                break
            while data:
                count = sys.stderr.write(data.decode('utf-8'))
                data = data[count:]
    finally:
        stream.close()


class ClassicMode(unittest.TestCase):
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
        self.conn = None

    def test_piped_server(self):
        # this causes the following lines to be printed to stderr on Windows:
        #
        # close failed in file object destructor:
        #     IOError: [Errno 9] Bad file descriptor
        # close failed in file object destructor:
        #     IOError: [Errno 9] Bad file descriptor
        #
        # this is because the pipe objects that hold the child process' stdin
        # and stdout were disowned by Win32PipeStream (it forcefully takes
        # ownership of the file handles). so when the low-level pipe objects
        # are gc'ed, they cry that their fd is already closed. this is all
        # considered harmless, but there's no way to disable that message
        # to stderr
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
        conn = rpyc.classic.connect_subproc(server_file, stderr=PIPE)
        worker = rpyc.worker(splice_to_stderr, conn.proc.stderr)
        try:
            conn.modules.sys.path.append("xxx")
            self.assertEqual(conn.modules.sys.path.pop(-1), "xxx")
        except Exception:
            conn.proc.kill()
            conn.proc.wait()
            raise
        finally:
            conn.close()
            worker.join()
        self.assertEqual(conn.proc.wait(), 0)

    def test_buffiter(self):
        bi = rpyc.buffiter(self.conn.builtin.range(10000))
        self.assertEqual(list(bi), list(range(10000)))

    def test_classic(self):
        self.conn.execute("x = 5")
        self.assertEqual(self.conn.namespace["x"], 5)
        self.assertEqual(self.conn.eval("1+x"), 6)

    def test_mock_connection(self):
        from rpyc.utils.classic import MockClassicConnection
        import sys
        import xml.dom.minidom
        conn = MockClassicConnection()
        self.assertTrue(conn.modules.sys is sys)
        self.assertTrue(conn.modules["xml.dom.minidom"].Element is xml.dom.minidom.Element)
        self.assertTrue(conn.builtin.open is open)
        self.assertEqual(conn.eval("2+3"), 5)

    def test_modules(self):
        self.assertIn('tests.test_magic', self.conn.modules)
        self.assertNotIn('test_badmagic', self.conn.modules)
        self.assertIsNone(self.conn.builtins.locals()['self']._last_traceback)


if __name__ == "__main__":
    unittest.main()
