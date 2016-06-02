import unittest
from rpyc.utils.multiprocessing import count
from multiprocessing import Process

class TestMpCount(unittest.TestCase):
    def setUp(self):
        self.c = count(0)
    def test_counter_increase(self):
        def p_start(test_obj):
            next(test_obj.c)
        procs = []
        for i in range(10):
            p = Process(target=p_start, args=(self,))
            procs.append(p)
            p.start()
        for p in procs:
            p.join()
        assert next(self.c) == 10

    def test_counter_start_value(self):
        c1 = count(1)
        assert next(c1) == 1
        assert next(c1) == 2
        c = count()
        assert next(c) == 0
        assert next(c) == 1

