import math
import time
from threading import Thread

import rpyc
import unittest

from rpyc import ThreadedServer
from rpyc.security.exposer import expose

on_connect_called = False
on_disconnect_called = False

class MyMeta(type):
    def spam(self):
        return self.__name__ * 5

class MyClass(object):
    __metaclass__ = MyMeta

if not isinstance(MyMeta, MyMeta):
    # python 3 compatibility
    MyClass = MyMeta(MyClass.__name__, MyClass.__bases__, dict(MyClass.__dict__))

@expose(inherit=rpyc.Service)
class MyService(rpyc.Service):
    def on_connect(self):
        global on_connect_called
        on_connect_called = True

    def on_disconnect(self):
        global on_disconnect_called
        on_disconnect_called = True

    @expose
    def distance(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)

    @expose
    def getlist(self):
        return [1, 2, 3]

    def foobar(self):
        assert False

    @expose
    def getmeta(self):
        return MyClass()


class TestCustomService(unittest.TestCase):
    def setUp(self):
        config = {"allow_safe_attrs":False,
                  "allow_exposed_attrs":False,
                  "allow_unsafe_calls":False}

        self.server = ThreadedServer(MyService, port = 0, protocol_config = config)
        self.thd = Thread(target = self.server.start)
        self.thd.start()
        time.sleep(1)

        global on_connect_called
        self.conn = rpyc.connect("localhost", self.server.port)

        self.conn.root # this will block until the service is initialized,
        # so we can be sure on_connect_called is True by that time
        self.assertTrue(on_connect_called)
        on_connect_called = False

    def tearDown(self):
        global on_disconnect_called
        self.conn.close()
        self.server.close()
        self.thd.join()

        time.sleep(0.5) # this will wait a little, making sure
        # on_disconnect_called is already True
        self.assertTrue(on_disconnect_called)
        on_disconnect_called = False

    def test_aliases(self):
        print( "service name: %s" % (self.conn.root.get_service_name(),) )

    def test_distance(self):
        self.assertEqual(self.conn.root.distance((2,7), (5,11)) , 5)

    def test_attributes(self):
        self.conn.root.distance
        self.conn.root.getlist
        # this is not an exposed attribute:
        self.assertRaises(AttributeError, lambda: self.conn.root.foobar())

    def test_metaclasses(self):
        x = self.conn.root.getmeta()
        print( x )

if __name__ == "__main__":
    unittest.main()


