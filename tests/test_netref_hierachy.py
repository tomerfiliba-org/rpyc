import os
import rpyc
import tempfile
from rpyc.utils.server import ThreadedServer, ThreadPoolServer
from rpyc import SlaveService
import unittest


class MyMeta(type):

    def spam(self):
        return self.__name__ * 5


class MyClass(object):
    __metaclass__ = MyMeta


class MyService(rpyc.Service):
    on_connect_called = False
    on_disconnect_called = False

    def on_connect(self, conn):
        self.on_connect_called = True

    def on_disconnect(self, conn):
        self.on_disconnect_called = True

    def exposed_distance(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def exposed_getlist(self):
        return [
            1, 2, 3]

    def foobar(self):
        assert False

    def exposed_getmeta(self):
        return MyClass()

    def exposed_instance(self, inst, cls):
        return isinstance(inst, cls)


class Test_Netref_Hierarchy(unittest.TestCase):

    def setUp(self):
        self.server = ThreadedServer(SlaveService, port=18878, auto_register=False)
        self.server.logger.quiet = False
        self.server._start_in_thread()

    def tearDown(self):
        self.server.close()

    def test_instancecheck_across_connections(self):
        conn = rpyc.classic.connect('localhost', port=18878)
        conn2 = rpyc.classic.connect('localhost', port=18878)
        conn.execute('import test_magic')
        conn2.execute('import test_magic')
        foo = conn.modules.test_magic.Foo()
        bar = conn.modules.test_magic.Bar()
        self.assertTrue(isinstance(foo, conn.modules.test_magic.Foo))
        self.assertTrue(isinstance(bar, conn2.modules.test_magic.Bar))
        self.assertFalse(isinstance(bar, conn.modules.test_magic.Foo))
        with self.assertRaises(TypeError):
            isinstance(conn.modules.test_magic.Foo, bar)
        conn.close()
        conn2.close()

    def test_classic(self):
        conn = rpyc.classic.connect_thread()
        x = conn.builtin.list((1, 2, 3, 4))
        self.assertTrue(isinstance(x, list))
        self.assertTrue(isinstance(x, rpyc.BaseNetref))
        with self.assertRaises(TypeError):
            isinstance([], x)
        i = 0
        self.assertTrue(type(x).__getitem__(x, i) == x.__getitem__(i))
        _builtins = conn.modules.builtins if rpyc.lib.compat.is_py_3k else conn.modules.__builtin__
        self.assertEqual(repr(_builtins.float.__class__), repr(type))
        self.assertEqual(repr(type(_builtins.float)), repr(type(_builtins.type)))

    def test_instancecheck_list(self):
        service = MyService()
        conn = rpyc.connect_thread(remote_service=service)
        conn.root
        remote_list = conn.root.getlist()
        self.assertTrue(conn.root.instance(remote_list, list))
        conn.close()

    def test_StandardError(self):
        conn = rpyc.classic.connect_thread()
        _builtins = conn.modules.builtins if rpyc.lib.compat.is_py_3k else conn.modules.__builtin__
        self.assertTrue(isinstance(_builtins.Exception(), _builtins.BaseException))
        self.assertTrue(isinstance(_builtins.Exception(), _builtins.Exception))
        self.assertTrue(isinstance(_builtins.Exception(), BaseException))
        self.assertTrue(isinstance(_builtins.Exception(), Exception))

    def test_modules(self):
        """
        >>> type(sys)
        <type 'module'>  # base case
        >>> type(conn.modules.sys)
        <netref class 'rpyc.core.netref.__builtin__.module'>  # matches base case
        >>> sys.__class__
        <type 'module'>  # base case
        >>> conn.modules.sys.__class__
        <type 'module'>  # matches base case
        >>> type(sys.__class__)
        <type 'type'>  # base case
        >>> type(conn.modules.sys.__class__)
        <netref class 'rpyc.core.netref.__builtin__.module'>  # doesn't match.  Should be a netref class of "type" (or maybe just <type 'type'> itself?)
        """
        import sys
        conn = rpyc.classic.connect_thread()
        self.assertEqual(repr(sys.__class__), repr(conn.modules.sys.__class__))
        # _builtin = sys.modules['builtins' if rpyc.lib.compat.is_py_3k else '__builtins__'].__name__
        # self.assertEqual(repr(type(conn.modules.sys)), "<netref class 'rpyc.core.netref.{}.module'>".format(_builtin))
        # self.assertEqual(repr(type(conn.modules.sys.__class__)), "<netref class 'rpyc.core.netref.{}.type'>".format(_builtin))


if __name__ == '__main__':
    unittest.main()
