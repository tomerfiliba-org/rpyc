import math
import time

import rpyc
import unittest


class MyMeta(type):
    def spam(self):
        return self.__name__ * 5


class MyClass(object):
    __metaclass__ = MyMeta


if not isinstance(MyMeta, MyMeta):
    # python 3 compatibility
    MyClass = MyMeta(MyClass.__name__, MyClass.__bases__, dict(MyClass.__dict__))


class MyService(rpyc.Service):
    on_connect_called = False
    on_disconnect_called = False
    on_about_to_close_called = False

    def on_connect(self, conn):
        self.on_connect_called = True

    def on_disconnect(self, conn):
        self.on_disconnect_called = True

    def exposed_on_about_to_close(self):
        self.on_about_to_close_called = True

    def exposed_distance(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def exposed_getlist(self):
        return [1, 2, 3]

    def foobar(self):
        assert False

    def exposed_getmeta(self):
        return MyClass()

    def exposed_instance(self, inst, cls):
        return isinstance(inst, cls)


def before_closed(root):
    root.on_about_to_close()


class TestCustomService(unittest.TestCase):
    config = {}

    def setUp(self):
        self.service = MyService()
        client_config = {"before_closed": before_closed, "close_catchall": False}
        self.conn = rpyc.connect_thread( remote_service=self.service, config=client_config)

        self.conn.root  # this will block until the service is initialized,
        # so we can be sure on_connect_called is True by that time
        self.assertTrue(self.service.on_connect_called)

    def tearDown(self):
        if not self.conn.closed:
            self.conn.close()
        time.sleep(0.5)  # this will wait a little, making sure
        # on_disconnect_called is already True
        self.assertTrue(self.service.on_disconnect_called)

    def test_before_closed(self):
        self.assertFalse(self.service.on_about_to_close_called)
        self.conn.close()
        self.assertTrue(self.service.on_about_to_close_called)

    def test_aliases(self):
        print("service name: %s" % (self.conn.root.get_service_name(),))

    def test_distance(self):
        assert self.conn.root.distance((2, 7), (5, 11)) == 5

    def test_attributes(self):
        self.conn.root.distance
        self.conn.root.exposed_distance
        self.conn.root.getlist
        self.conn.root.exposed_getlist
        # this is not an exposed attribute:
        self.assertRaises(AttributeError, lambda: self.conn.root.foobar())

    def test_safeattrs(self):
        x = self.conn.root.getlist()
        # self.require(x == [1, 2, 3]) -- can't compare remote objects, sorry
        # self.require(x * 2 == [1, 2, 3, 1, 2, 3])
        self.assertEqual([y * 2 for y in x], [2, 4, 6])

    def test_metaclasses(self):
        x = self.conn.root.getmeta()
        print(x)

    def test_instancecheck_list(self):
        remote_list = self.conn.root.getlist()
        self.assertTrue(self.conn.root.instance(remote_list, list))


if __name__ == "__main__":
    unittest.main()
