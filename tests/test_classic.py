import rpyc
import unittest


class ClassicMode(unittest.TestCase):
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
        conn = rpyc.classic.connect_subproc()
        conn.modules.sys.path.append("xxx")
        self.assertEqual(conn.modules.sys.path.pop(-1), "xxx")
        conn.close()
        self.assertEqual(conn.proc.wait(), 0)

    def test_buffiter(self):
        bi = rpyc.buffiter(self.conn.builtin.range(10000))
        self.assertEqual(list(bi), list(range(10000)))

    def test_classic(self):
        print( self.conn.modules.sys )
        print( self.conn.modules["xml.dom.minidom"].parseString("<a/>") )
        self.conn.execute("x = 5")
        self.assertEqual(self.conn.namespace["x"], 5)
        self.assertEqual(self.conn.eval("1+x"), 6)

    def test_isinstance(self):
        x = self.conn.builtin.list((1,2,3,4))
        print( x )
        print( type(x) )
        print( x.__class__ )
        self.assertTrue(isinstance(x, list))
        self.assertTrue(isinstance(x, rpyc.BaseNetref))


if __name__ == "__main__":
    unittest.main()


