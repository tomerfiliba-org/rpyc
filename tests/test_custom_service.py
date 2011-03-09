import math
import time

import rpyc

on_connect_called = False
on_disconnect_called = False

class MyMeta(type):
    def spam(self):
        return self.__name__ * 5

class MyClass(object):
    __metaclass__ = MyMeta


class MyService(rpyc.Service):
    def on_connect(self):
        global on_connect_called
        on_connect_called = True

    def on_disconnect(self):
        global on_disconnect_called
        on_disconnect_called = True
    
    def exposed_distance(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    def exposed_getlist(self):
        return [1, 2, 3]
    
    def foobar(self):
        assert False
    
    def exposed_getmeta(self):
        return MyClass()

class Test_CustomService(object):
    config = {}

    def setup(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)
        self.conn.root # this will block until the service is initialized,
        # so we can be sure on_connect_called is True by that time
        assert on_connect_called

    def teardown(self):
        self.conn.close()
        time.sleep(0.5) # this will wait a little, making sure 
        # on_disconnect_called is already True
        assert on_disconnect_called
    
    def test_aliases(self):
        print "service name: {0}".format(self.conn.root.get_service_name())
    
    def test_distance(self):
        assert self.conn.root.distance((2,7), (5,11)) == 5
    
    def test_attributes(self):
        self.conn.root.distance
        self.conn.root.exposed_distance
        self.conn.root.getlist
        self.conn.root.exposed_getlist
        try:
            self.conn.root.foobar() # this is not an exposed attribute
        except AttributeError, ex:
            print "exception is: {0}".format(ex)
        else:
            self.fail("expected AttributeError")
    
    def test_safeattrs(self):
        x = self.conn.root.getlist()
        #self.require(x == [1, 2, 3]) -- can't compare remote objects, sorry
        #self.require(x * 2 == [1, 2, 3, 1, 2, 3])
        assert [y*2 for y in x] == [2, 4, 6]
    
    def test_metaclasses(self):
        x = self.conn.root.getmeta()
        print x