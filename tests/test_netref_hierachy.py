import math
import rpyc
from rpyc.utils.server import ThreadedServer
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

    def exposed_getnonetype(self):
        """ About the unit test - what's common to types.MethodType and NoneType is that both are
        not accessible via builtins. So the unit test I've added in 108ff8e was enough to 
        my understanding (implement it with NoneType because that's more easily "created") """
        return type(None)


class Test_Netref_Hierarchy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadedServer(SlaveService, port=18878, auto_register=False)
        cls.server.logger.quiet = False
        cls.server._start_in_thread()

    def setUp(self):
        self.conn = rpyc.classic.connect('localhost', port=18878)
        self.conn2 = None

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def tearDown(self):
        self.conn.close()
        if self.conn2 is not None:
            self.conn2.close()

    def test_instancecheck_across_connections(self):
        self.conn2 = rpyc.classic.connect('localhost', port=18878)
        self.conn.execute('import test_magic')
        self.conn2.execute('import test_magic')
        foo = self.conn.modules.test_magic.Foo()
        bar = self.conn.modules.test_magic.Bar()
        self.assertTrue(isinstance(foo, self.conn.modules.test_magic.Foo))
        self.assertTrue(isinstance(bar, self.conn2.modules.test_magic.Bar))
        self.assertFalse(isinstance(bar, self.conn.modules.test_magic.Foo))
        with self.assertRaises(TypeError):
            isinstance(self.conn.modules.test_magic.Foo, bar)

    def test_classic(self):
        x = self.conn.builtin.list((1, 2, 3, 4))
        self.assertTrue(isinstance(x, list))
        self.assertTrue(isinstance(x, rpyc.BaseNetref))
        with self.assertRaises(TypeError):
            isinstance([], x)
        i = 0
        self.assertTrue(type(x).__getitem__(x, i) == x.__getitem__(i))
        _builtins = self.conn.modules.builtins if rpyc.lib.compat.is_py_3k else self.conn.modules.__builtin__
        self.assertEqual(repr(_builtins.float.__class__), repr(type))
        self.assertEqual(repr(type(_builtins.float)), repr(type(_builtins.type)))

    def test_instancecheck_list(self):
        service = MyService()
        conn = rpyc.connect_thread(remote_service=service)
        conn.root
        remote_list = conn.root.getlist()
        self.assertTrue(conn.root.instance(remote_list, list))
        conn.close()

    def test_instancecheck_none(self):
        """
        test for the regression reported in https://github.com/tomerfiliba-org/rpyc/issues/426
        """
        service = MyService()
        conn = rpyc.connect_thread(remote_service=service)
        remote_NoneType = conn.root.getnonetype()
        self.assertTrue(isinstance(None, remote_NoneType))
        conn.close()

    def test_StandardError(self):
        _builtins = self.conn.modules.builtins if rpyc.lib.compat.is_py_3k else self.conn.modules.__builtin__
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
        <netref class 'rpyc.core.netref.__builtin__.module'>  # doesn't match.
        # ^Should be a netref class of "type" (or maybe just <type 'type'> itself?)
        """
        import sys
        self.assertEqual(repr(sys.__class__), repr(self.conn.modules.sys.__class__))
        # _builtin = sys.modules['builtins' if rpyc.lib.compat.is_py_3k else '__builtins__'].__name__
        # self.assertEqual(repr(type(self.conn.modules.sys)),
        #                  "<netref class 'rpyc.core.netref.{}.module'>".format(_builtin))
        # self.assertEqual(repr(type(self.conn.modules.sys.__class__)),
        #                  "<netref class 'rpyc.core.netref.{}.type'>".format(_builtin))


if __name__ == '__main__':
    unittest.main()
