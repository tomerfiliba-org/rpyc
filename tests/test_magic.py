import sys
import rpyc
import unittest

is_py3 = sys.version_info >= (3,)


class Meta(type):

    def __hash__(self):
        return 4321


Base = Meta('Base', (object,), {})


class Foo(Base):
    def __hash__(self):
        return 1234


class Bar(Foo):
    pass


class Mux(Foo):
    def __eq__(self, other):
        return True


class TestContextManagers(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.classic.connect_thread()

    def tearDown(self):
        self.conn.close()

    def test_hash_class(self):
        hesh = self.conn.builtins.hash
        mod = self.conn.modules.test_magic
        self.assertEqual(hash(mod.Base), 4321)
        self.assertEqual(hash(mod.Foo), 4321)
        self.assertEqual(hash(mod.Bar), 4321)
        self.assertEqual(hash(mod.Base().__class__), 4321)
        self.assertEqual(hash(mod.Foo().__class__), 4321)
        self.assertEqual(hash(mod.Bar().__class__), 4321)

        basecl_ = mod.Foo().__class__.__mro__[1]
        object_ = mod.Foo().__class__.__mro__[2]
        self.assertEqual(hash(basecl_), hesh(basecl_))
        self.assertEqual(hash(object_), hesh(object_))
        self.assertEqual(hash(object_), hesh(self.conn.builtins.object))

    def test_hash_obj(self):
        hesh = self.conn.builtins.hash
        mod = self.conn.modules.test_magic
        obj = mod.Base()

        self.assertNotEqual(hash(obj), 1234)
        self.assertNotEqual(hash(obj), 4321)
        self.assertEqual(hash(obj), hesh(obj))

        self.assertEqual(hash(mod.Foo()), 1234)
        self.assertEqual(hash(mod.Bar()), 1234)
        if is_py3:
            # py3 implicitly adds '__hash__=None' during class construction
            # if '__eq__ is defined:
            self.assertRaises(TypeError, lambda: hash(mod.Mux()))
        else:
            self.assertEqual(hash(mod.Mux()), 1234)


if __name__ == "__main__":
    unittest.main()
