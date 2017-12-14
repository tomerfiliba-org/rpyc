#Test the on_box method hook of rpyc.Service

import rpyc
import unittest

class MyService(rpyc.Service):
    def on_box(self, obj):
        if obj == 2:
            obj = None
        return obj

    def exposed_get_values(self):
        return (1,3,4,5,2,6)

class TestCustomService(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)
        self.conn.root # this will block until the service is initialized,

    def tearDown(self):
        self.conn.close()

    def test_on_box(self):
        x = self.conn.root.get_values()
        self.assertTrue( x == (1,3,4,5,None,6) )

if __name__ == "__main__":
    unittest.main()


