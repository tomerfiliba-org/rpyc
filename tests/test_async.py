import time

from nose.tools import raises

import rpyc

class Test_Async(object):
    def __init__(self):
        pass

    def setup(self):
        self.conn = rpyc.classic.connect_thread()
        self.a_sleep = rpyc.async(self.conn.modules.time.sleep)
        self.a_int = rpyc.async(self.conn.modules.__builtin__.int)

    def teardown(self):
        self.conn.close()

    def test_asyncresult_api(self):
        res = self.a_sleep(2)
        assert not res.ready
        res.wait()
        assert res.ready
        assert not res.expired
        assert not res.error
        assert res.value is None

    def test_asyncresult_expiry(self):
        res = self.a_sleep(5)
        res.set_expiry(4)
        t0 = time.time()
        try:
            res.wait()
        except rpyc.AsyncResultTimeout:
            dt = time.time() - t0
        else:
            assert False, "expected AsyncResultTimeout"
        print( "timed out after %s" % (dt,) )
        assert 3.9 <= dt <= 4.1

    def test_asyncresult_callbacks(self):
        res = self.a_sleep(2)
        visited = []

        def f(res):
            assert res.ready
            assert not res.error
            visited.append("f")

        def g(res):
            visited.append("g")

        res.add_callback(f)
        res.add_callback(g)
        res.wait()
        assert set(visited) == set(["f", "g"])

    @raises(rpyc.AsyncResultTimeout)
    def test_timed(self):
        timed_sleep = rpyc.timed(self.a_sleep, 5)
        print( timed_sleep )
        res = timed_sleep(3)
        print( res.value )
        res = timed_sleep(7)
        print( res.value )

    @raises(ValueError)
    def test_exceptions(self):
        res = self.a_int("foo")
        res.wait()
        assert res.error
        res.value

