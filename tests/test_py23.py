import os
import rpyc
import unittest


class ClassicMode(unittest.TestCase):
    def setUp(self):
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
        self.conn = connect_another_py(server_file)

    def tearDown(self):
        self.conn.close()
        self.assertEqual(self.conn.proc.wait(), 0)
        self.conn = None

    def test_sys_path(self):
        self.conn.modules.sys.path.append("xxx")
        self.assertEqual(self.conn.modules.sys.path.pop(-1), "xxx")

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


def connect_another_py(server_file = None):
    """Runs an RPyC classic server as a subprocess and returns an RPyC
    connection to it over stdio

    :param server_file: The full path to the server script (``rpyc_classic.py``).
                        If not given, ``which rpyc_classic.py`` will be attempted.

    :returns: an RPyC connection exposing ``SlaveService``
    """
    from rpyc.utils import factory
    from rpyc.lib.compat import is_py3k
    from rpyc.core.service import ClassicService
    if server_file is None:
        server_file = os.popen("which rpyc_classic.py").read().strip()
        if not server_file:
            raise ValueError("server_file not given and could not be inferred")
    py_version = "-2" if is_py3k else "-3"
    print("connecting to py %s" % py_version)
    return factory.connect_subproc(["py", py_version, "-u", server_file, "-q", "-m", "stdio"], ClassicService)


if __name__ == "__main__":
    unittest.main()
