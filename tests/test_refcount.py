import rpyc
import gc
import unittest


class TestRefcount(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.classic.connect_thread()

    def tearDown(self):
        self.conn.close()

    def test_refcount(self):
        self.conn.execute("""
deleted_objects = []

class DummyObject(object):
    def __init__(self, name):
        self.name = name
    def __del__(self):
        deleted_objects.append(self.name)""")
        rDummyObject = self.conn.namespace["DummyObject"]
        d1 = rDummyObject("d1")
        d2 = rDummyObject("d2")
        d3 = rDummyObject("d3")
        d4 = rDummyObject("d4") #@UnusedVariable
        d2_copy = d2
        del d1
        del d3
        gc.collect()
        self.assertEqual(set(self.conn.namespace["deleted_objects"]), set(["d1", "d3"]))
        del d2
        gc.collect()
        self.assertEqual(set(self.conn.namespace["deleted_objects"]), set(["d1", "d3"]))
        del d2_copy
        gc.collect()
        self.assertEqual(set(self.conn.namespace["deleted_objects"]), set(["d1", "d2", "d3"]))


if __name__ == "__main__":
    unittest.main()



