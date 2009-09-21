from testbase import TestBase
import rpyc
import time


class AsyncTest(TestBase):
    def setup(self):
        self.conn = rpyc.classic.connect_thread()
        self.a_sleep = rpyc.async(self.conn.modules.time.sleep)
        self.a_int = rpyc.async(self.conn.modules.__builtin__.int)
    def cleanup(self):
        self.conn.close()

    def step_asyncresult_api(self):
        res = self.a_sleep(2)
        self.require(not res.ready)
        res.wait()
        self.require(res.ready)
        self.require(not res.expired)
        self.require(not res.error)
        self.require(res.value is None) # sleep returns None

    def step_asyncresult_expiry(self):
        res = self.a_sleep(5)
        res.set_expiry(4)
        t0 = time.time()
        try:
            res.wait()
        except rpyc.AsyncResultTimeout:
            dt = time.time() - t0
        else:
            self.fail("expected AsyncResultTimeout")
        self.log("timed out after %s", dt)
        self.require(3.9 <= dt <= 4.1)
    
    def step_asyncresult_callbacks(self):
        res = self.a_sleep(2)
        visited = []
        def f(res):
            self.require(res.ready)
            self.require(not res.error)
            visited.append("f")
        def g(res):
            visited.append("g")
        res.add_callback(f)
        res.add_callback(g)
        res.wait()
        self.require(set(visited) == set(["f", "g"]))
    
    def step_timed(self):
        timed_sleep = rpyc.timed(self.a_sleep, 5)
        self.log(timed_sleep)
        res = timed_sleep(3)
        res.value
        res = timed_sleep(7)
        try:
            res.value
        except rpyc.AsyncResultTimeout:
            pass
        else:
            self.fail("expected AsyncResultTimeout")
    
    def step_exceptions(self):
        res = self.a_int("foo")
        res.wait()
        self.require(res.error)
        try:
            res.value
        except ValueError:
            pass
        else:
            self.fail("expected TypeError")


if __name__ == "__main__":
    AsyncTest.run()




