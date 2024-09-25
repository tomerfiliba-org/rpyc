import inspect
import math
import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
from rpyc.core import netref
import unittest


logger = rpyc.lib.setup_logger()


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


class TestBaseNetrefMRO(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.classic.connect_thread()

    def tearDown(self):
        self.conn.close()
        self.conn = None

    def test_mro(self):
        # TODO: netref.class_factory, redesign to register builtin types and better handle generic-aliases/types
        #   - components to explore: abc.ABCMeta, abc.ABC.register types
        #   - add mro test for netrefs to remote builtins
        self.assertEqual(netref.NetrefMetaclass.__mro__, (netref.NetrefMetaclass, type, object))

    def test_basenetref(self):
        self.assertIsInstance(netref.BaseNetref, netref.NetrefMetaclass)
        self.assertIsInstance(netref.BaseNetref, object)
        mro = inspect.getmro(netref.BaseNetref)
        self.assertEqual(mro, (netref.BaseNetref, object))

    def test_builtins_dict_netref(self):
        cls = netref.builtin_classes_cache['builtins.dict']
        mro_netref = inspect.getmro(cls)
        mro_dict = inspect.getmro(dict)
        logger.debug('\n')
        logger.debug(f'dict_netref: {mro_netref}')
        logger.debug(f'dict:        {mro_dict}')
        self.conn.execute("dict_ = dict(a=0xd35db33f)")
        remote_dict = self.conn.namespace['dict_']
        logger.debug(f'remote_dict: {remote_dict}')
        self.assertEqual(remote_dict['a'], 3546133311)


class Test_Netref_Hierarchy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadedServer(SlaveService, port=18878, auto_register=False)
        cls.server.logger.quiet = False
        cls.server._start_in_thread()

    def setUp(self):
        self.conn = rpyc.classic.connect('localhost', port=18878)

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def tearDown(self):
        self.conn.close()

    def test_instancecheck_across_connections(self):
        self.conn2 = rpyc.classic.connect('localhost', port=18878)
        self.conn.execute('import tests.test_magic')
        self.conn2.execute('import tests.test_magic')
        foo = self.conn.modules.tests.test_magic.Foo()
        bar = self.conn.modules.tests.test_magic.Bar()
        self.assertTrue(isinstance(foo, self.conn.modules.tests.test_magic.Foo))
        self.assertTrue(isinstance(bar, self.conn2.modules.tests.test_magic.Bar))
        self.assertFalse(isinstance(bar, self.conn.modules.tests.test_magic.Foo))
        with self.assertRaises(TypeError):
            isinstance(self.conn.modules.tests.test_magic.Foo, bar)

    def test_classic(self):
        x = self.conn.builtin.list((1, 2, 3, 4))
        self.assertTrue(isinstance(x, list))
        self.assertTrue(isinstance(x, rpyc.BaseNetref))
        with self.assertRaises(TypeError):
            isinstance([], x)
        i = 0
        self.assertTrue(type(x).__getitem__(x, i) == x.__getitem__(i))

    def test_builtins(self):
        _builtins = self.conn.modules.builtins
        self.assertEqual(repr(_builtins.dict), repr(dict))  # Check repr behavior of netref matches local
        self.assertEqual(repr(type(_builtins.dict.__class__)), repr(type))  # Check netref __class__ is type
        self.assertIs(type(_builtins.dict.__class__), type)
        # Check class descriptor for netrefs
        dict_ = _builtins.dict(space='remote')
        self.assertIs(type(dict_).__dict__['__class__'].instance, dict)
        self.assertIs(type(dict_).__dict__['__class__'].owner, type)

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
        >>> type(unittest)
        <class 'module'>
        >>> type(self.conn.modules.unittest)
        <netref class 'rpyc.core.netref.unittest'>  # reflects that it is a proxy object to unittest
        >>> unittest.__class__
        <class 'module'>  # base case
        >>> conn.modules.unittest.__class__
        <class 'module'>  # matches base case
        >>> type(unittest.__class__)
        <class 'type'>  # base case
        >>> type(conn.modules.unittest.__class__)
        <class 'type'>  # matches base case
        """
        # instance module assertions
        self.assertEqual(repr(self.conn.modules.unittest), repr(unittest))
        self.assertEqual(repr(type(self.conn.modules.unittest)), "<netref class 'rpyc.core.netref.unittest'>")
        self.assertIs(self.conn.modules.unittest.__class__, type(unittest))
        self.assertIs(type(self.conn.modules.unittest.__class__), type)
        # class module assertions
        remote_module_cls = self.conn.modules.builtins.type(self.conn.modules.sys)
        remote_module_cls_id = self.conn.modules.builtins.id(remote_module_cls)
        self.assertEqual(repr(remote_module_cls), "<class 'module'>")
        self.assertEqual(remote_module_cls.____id_pack__, ('builtins.module', remote_module_cls_id, 0))


    def test_proxy_instancecheck(self):
        self.assertIsInstance(self.conn.modules.builtins.RuntimeError(), Exception)
        # TODO: below should pass
        # self.assertIsInstance(self.conn.modules.builtins.RuntimeError(), self.conn.modules.builtins.Exception)


if __name__ == '__main__':
    unittest.main()
