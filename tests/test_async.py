import time
import unittest
import rpyc

class TestAsync(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.classic.connect_thread()
        self.a_sleep = rpyc.async(self.conn.modules.time.sleep)
        self.a_int = rpyc.async(self.conn.builtin.int)

    def tearDown(self):
        self.conn.close()
    
    def test_asyncresult_api(self):
        res = self.a_sleep(2)
        self.assertFalse(res.ready)
        res.wait()
        self.assertTrue(res.ready)
        self.assertFalse(res.expired)
        self.assertFalse(res.error)
        self.assertEqual(res.value, None)

    def test_asyncresult_expiry(self):
        res = self.a_sleep(5)
        res.set_expiry(4)
        t0 = time.time()
        self.assertRaises(rpyc.AsyncResultTimeout, res.wait)
        dt = time.time() - t0
        #print( "timed out after %s" % (dt,) )
        self.assertTrue(dt >= 3.5, str(dt))
        self.assertTrue(dt <= 4.5, str(dt))

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
        self.assertEqual(set(visited), set(["f", "g"]))
        
    def test_timed(self):
        timed_sleep = rpyc.timed(self.conn.modules.time.sleep, 5)
        res = timed_sleep(3)
        res.value
        res = timed_sleep(7)
        self.assertRaises(rpyc.AsyncResultTimeout, lambda: res.value)

    def test_exceptions(self):
        res = self.a_int("foo")
        res.wait()
        self.assertTrue(res.error)
        self.assertRaises(ValueError, lambda: res.value)

if __name__ == "__main__":
    unittest.main()

