#!/usr/bin/env python
import threading
import time
import unittest
import rpyc

class MyService(rpyc.Service):
    class exposed_Invoker(object):
        def __init__(self, callback, interval):
            self.callback = rpyc.async(callback)
            self.interval = interval
            self.active = True
            self.thread = threading.Thread(target=self.work)
            self.thread.setDaemon(True)
            self.thread.start()

        def exposed_stop(self):
            self.active = False
            self.thread.join()

        def work(self):
            while self.active:
                self.callback(time.time())
                time.sleep(self.interval)

    def exposed_foo(self, x):
        time.sleep(2)
        return x * 17

class Test_Multithreaded(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)
        self.bgserver = rpyc.BgServingThread(self.conn)

    def tearDown(self):
        self.bgserver.stop()
        self.conn.close()

    def test_invoker(self):
        counter = [0]
        def callback(x):
            counter[0] += 1
            print( "callback %s" % (x,) )
        invoker = self.conn.root.Invoker(callback, 1)
        # 3 * 2sec = 6 sec = ~6 calls to callback
        for i in range(3):
            print( "foo%s = %s" % (i, self.conn.root.foo(i)) )
        invoker.stop()
        print( "callback called %s times" % (counter[0],) )
        self.assertTrue(counter[0] >= 5)


if __name__ == "__main__":
    unittest.main()



