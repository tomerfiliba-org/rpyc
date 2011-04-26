import rpyc

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


class Test_Attributes(object):
    def setup(self):
        self.conn = rpyc.classic.connect_thread()

    def teardown(self):
        self.conn.close()

    def test_properties(self):
        p = self.conn.modules["test_attributes"].Properties()
        print( p.counter )       # 1
        print( p.counter )       # 2
        print( p.counter )       # 3
        assert p.counter == 4    # 4

