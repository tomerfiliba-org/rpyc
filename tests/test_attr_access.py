import rpyc
import copy
import unittest
from rpyc.utils.server import ThreadedServer


class MyClass(object):
    def __add__(self, other):
        return self.foo() + str(other)

    def foo(self):
        return "foo"

    def bar(self):
        return "bar"

    def spam(self):
        return "spam"

    def _privy(self):
        return "privy"

    def exposed_foobar(self):
        return "Fee Fie Foe Foo"


class YourClass(object):
    def lala(self):
        return MyClass()

    def baba(self):
        return "baba"

    def gaga(self):
        return "gaga"


try:
    long
except NameError:
    long = int
    unicode = str

try:
    bytes
except NameError:
    bytes = str


class Protector(object):
    def __init__(self, safetypes=(int, list, bool, tuple, str, float, long, unicode, bytes)):
        self._safetypes = set(safetypes)
        self._typereg = {}

    def register(self, typ, attrs):
        self._typereg[typ] = frozenset(attrs)

    def wrap(self, obj):
        class Restrictor(object):
            def __call__(_, *args, **kwargs):
                return self.wrap(obj(*args, **kwargs))

            def _rpyc_getattr(_, name):
                if type(obj) not in self._safetypes:
                    attrs = self._typereg.get(type(obj), ())
                    if name not in attrs:
                        raise AttributeError(name)
                obj2 = getattr(obj, name)
                return self.wrap(obj2)
            __getattr__ = _rpyc_getattr
        return Restrictor()


SVC_RESTRICTED = ["exposed_foobar", "__add__", "_privy", "foo", "bar"]


class MyService(rpyc.Service):
    exposed_MyClass = MyClass

    def exposed_get_one(self):
        return rpyc.restricted(MyClass(), SVC_RESTRICTED)

    def exposed_get_two(self):
        protector = Protector()
        protector.register(MyClass, SVC_RESTRICTED)
        protector.register(YourClass, ["lala", "baba"])
        return protector.wrap(YourClass())


class TestRestricted(unittest.TestCase):
    def setUp(self):
        self.server = ThreadedServer(MyService)
        self.thd = self.server._start_in_thread()
        self.conn = rpyc.connect("localhost", self.server.port)

    def tearDown(self):
        self.conn.close()
        while self.server.clients:
            pass
        self.server.close()
        self.thd.join()

    def test_restricted(self):
        obj = self.conn.root.get_one()
        self.assertEqual(obj.foo(), "foo")
        self.assertEqual(obj.bar(), "bar")
        self.assertEqual(obj.__add__("bar"), "foobar")
        self.assertEqual(obj._privy(), "privy")
        self.assertEqual(obj.exposed_foobar(), "Fee Fie Foe Foo")
        self.assertRaises(AttributeError, lambda: obj.spam)

    def test_restricted2(self):
        self.server.protocol_config = {'allow_public_attrs': False}
        obj = self.conn.root.get_one()
        self.assertEqual(obj.foo(), "foo")
        self.assertEqual(obj.bar(), "bar")
        self.assertEqual(obj.__add__("bar"), "foobar")
        self.assertEqual(obj._privy(), "privy")
        self.assertRaises(AttributeError, lambda: obj.spam)


class TestConfigAllows(unittest.TestCase):
    def setUp(self):
        self.cfg = self._reset_cfg()
        self.server = ThreadedServer(MyService, port=0)
        self.thd = self.server._start_in_thread()
        self.conn = rpyc.connect("localhost", self.server.port)

    def tearDown(self):
        self.conn.close()
        while self.server.clients:
            pass
        self.server.close()
        self.thd.join()

    def _reset_cfg(self):
        self.cfg = copy.copy(rpyc.core.protocol.DEFAULT_CONFIG)
        return self.cfg

    def _get_myclass(self, proto_config):
        self.conn.close()
        self.server.protocol_config.update(proto_config)
        self.conn = rpyc.connect("localhost", self.server.port)
        return self.conn.root.MyClass()

    def test_default_config(self):
        obj = self._get_myclass(self.cfg)
        self.assertEqual(obj + 'bar', "foobar")
        self.assertEqual(obj.foobar(), "Fee Fie Foe Foo")
        self.assertEqual(obj.exposed_foobar(), "Fee Fie Foe Foo")
        self.assertRaises(AttributeError, lambda: obj._privy)
        self.assertRaises(AttributeError, lambda: obj.foo)
        self.assertRaises(AttributeError, lambda: obj.bar)
        self.assertRaises(AttributeError, lambda: obj.spam)

    def test_allow_all(self):
        self._reset_cfg()
        self.cfg['allow_all_attrs'] = True
        obj = self._get_myclass(self.cfg)
        self.assertEqual(obj + 'bar', "foobar")
        self.assertEqual(obj.__add__("bar"), "foobar")
        self.assertEqual(obj._privy(), "privy")
        self.assertEqual(obj.foobar(), "Fee Fie Foe Foo")
        self.assertEqual(obj.exposed_foobar(), "Fee Fie Foe Foo")

    def test_allow_exposed(self):
        self._reset_cfg()
        self.cfg['allow_exposed_attrs'] = False
        try:
            self._get_myclass(self.cfg)  # returns obj, but ignored
            passed = False
        except Exception:
            passed = True
        self.assertEqual(passed, True)

    def test_allow_safe_attrs(self):
        self._reset_cfg()
        self.cfg['allow_safe_attrs'] = False
        obj = self._get_myclass(self.cfg)
        self.assertEqual(obj.foobar(), "Fee Fie Foe Foo")
        self.assertEqual(obj.exposed_foobar(), "Fee Fie Foe Foo")
        self.assertRaises(AttributeError, lambda: obj._privy)
        self.assertRaises(AttributeError, lambda: obj + 'bar')
        self.assertRaises(AttributeError, lambda: obj.foo)
        self.assertRaises(AttributeError, lambda: obj.bar)
        self.assertRaises(AttributeError, lambda: obj.spam)

    def test_allow_public_attrs(self):
        self._reset_cfg()
        self.cfg['allow_public_attrs'] = True
        obj = self._get_myclass(self.cfg)
        self.assertEqual(obj + 'bar', "foobar")
        self.assertEqual(obj.foo(), "foo")
        self.assertEqual(obj.bar(), "bar")
        self.assertEqual(obj.foobar(), "Fee Fie Foe Foo")
        self.assertEqual(obj.exposed_foobar(), "Fee Fie Foe Foo")
        self.assertRaises(AttributeError, lambda: obj._privy)

#    def test_type_protector(self):
#        obj = self.conn.root.get_two()
#        assert obj.baba() == "baba"
#        try:
#            obj.gaga()
#        except AttributeError:
#            pass
#        else:
#            assert False, "expected an attribute error!"
#        obj2 = obj.lala()
#        assert obj2.foo() == "foo"
#        assert obj2.spam() == "spam"
#        try:
#            obj.bar()
#        except AttributeError:
#            pass
#        else:
#            assert False, "expected an attribute error!"
#


if __name__ == "__main__":
    unittest.main()
