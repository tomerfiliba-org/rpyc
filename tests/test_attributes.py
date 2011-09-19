import rpyc
import unittest


class Properties(object):
    def __init__(self):
        self._x = 0

    @property
    def counter(self):
        self._x += 1
        return self._x

    @property
    def dont_touch_me(self):
        # reconstruct bug reported by Andrew Stromnov
        # http://groups.google.com/group/rpyc/msg/aa6110259481f194
        1/0


class TestAttributes(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.classic.connect_thread()

    def tearDown(self):
        self.conn.close()

    def test_properties(self):
        p = self.conn.modules["test_attributes"].Properties()
        print( p.counter )                # 1
        print( p.counter )                # 2
        print( p.counter )                # 3
        self.assertEqual(p.counter, 4)    # 4


if __name__ == "__main__":
    unittest.main()
