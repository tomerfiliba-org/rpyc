import rpyc


class Test_Classic(object):
    def setup(self):
        self.conn = rpyc.classic.connect_thread()

    def teardown(self):
        self.conn.close()

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

        conn2 = rpyc.classic.connect_subproc()
        conn2.modules.sys.path.append("xxx")
        assert conn2.modules.sys.path.pop(-1), "xxx"
        conn2.close()
        assert conn2.proc.wait() == 0

    def test_buffiter(self):
        bi = rpyc.buffiter(self.conn.modules.__builtin__.xrange(10000))
        assert list(bi) == range(10000)

    def test_classic(self):
        print( self.conn.modules.sys )
        print( self.conn.modules["xml.dom.minidom"].parseString("<a/>") )
        self.conn.execute("x = 5")
        assert self.conn.namespace["x"] == 5
        assert self.conn.eval("1+x") == 6

    def test_isinstance(self):
        x = self.conn.modules.__builtin__.range(10)
        print( x )
        print( type(x) )
        print( x.__class__ )
        assert isinstance(x, list)

