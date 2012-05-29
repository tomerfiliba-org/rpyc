import rpyc
import unittest
import time
from rpyc.utils.server import ThreadedServer
from threading import Thread


class MyClass(object):
    def foo(self):
        return "foo"
    def bar(self):
        return "bar"
    def spam(self):
        return "spam"

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
    def __init__(self, safetypes = (int, list, bool, tuple, str, float, long, unicode, bytes)):
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

class MyService(rpyc.Service):
    def exposed_get_one(self):
        return rpyc.restricted(MyClass(), ["foo", "bar"])
    
    def exposed_get_two(self):
        protector = Protector()
        protector.register(MyClass, ["foo", "spam"])
        protector.register(YourClass, ["lala", "baba"])
        return protector.wrap(YourClass())

class TestRestricted(unittest.TestCase):
    def setUp(self):
        self.server = ThreadedServer(MyService, port = 0)
        self.thd = Thread(target = self.server.start)
        self.thd.start()
        time.sleep(1)
        self.conn = rpyc.connect("localhost", self.server.port)

    def tearDown(self):
        self.conn.close()
        self.server.close()
        self.thd.join()

    def test_restricted(self):
        obj = self.conn.root.get_one()
        self.assertEqual(obj.foo(), "foo")
        self.assertEqual(obj.bar(), "bar")
        self.assertRaises(AttributeError, lambda: obj.spam)

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




