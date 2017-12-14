#Test the on_call method hook of rpyc.Service

import rpyc
import inspect
import unittest

class MyService(rpyc.Service):
    def on_call(self, obj, args, kwargs):
        if inspect.isroutine(obj):
           return obj(*args, **kwargs)
        else:
            raise TypeError("Non-routine types not callable remotely.")

    def __call__(self):
        return True

    def exposed_test(self):
        return True

class TestCustomService(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)
        self.conn.root # this will block until the service is initialized,

    def tearDown(self):
        self.conn.close()

    def test_on_call(self):
        self.assertTrue(self.conn.root.test())
        valid=False
        try:
            self.conn.root()
        except TypeError as e:
            self.assertTrue("remotely" in str(e))
            valid=True
        self.assertTrue(valid)

if __name__ == "__main__":
    unittest.main()


