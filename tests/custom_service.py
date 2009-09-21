from __future__ import with_statement
from testbase import TestBase
import rpyc
import math
import time
from contextlib import contextmanager


on_connect_called = False
on_disconnect_called = False
on_context_exit = False

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
        return [1,2,3]
    
    def foobar(self):
        assert False
    
    @contextmanager
    def exposed_context(self, y):
        global on_context_exit
        try:
            yield 17 + y
        finally:
            on_context_exit = True
    
    def exposed_getmeta(self):
        return MyClass()

class CustomService(TestBase):
    config = {}
    def setup(self):
        self.conn = rpyc.connect_thread(remote_service = MyService)
        self.conn.root # this will block until the service is initialized,
        # so we can be sure on_connect_called is True by that time
        self.require(on_connect_called)
    def cleanup(self):
        self.conn.close()
        time.sleep(0.5) # this will wait a little, making sure 
        # on_disconnect_called is already True
        self.require(on_disconnect_called)
    
    def step_aliases(self):
        self.log("service name: %s", self.conn.root.get_service_name())
    
    def step_distance(self):
        self.require(self.conn.root.distance((2,7), (5,11)) == 5)
    
    def step_attributes(self):
        self.conn.root.distance
        self.conn.root.exposed_distance
        self.conn.root.getlist
        self.conn.root.exposed_getlist
        try:
            self.conn.root.foobar() # this is not an exposed attribute
        except AttributeError, ex:
            self.log("exception is: %s", ex)
        else:
            self.fail("expected AttributeError")
    
    def step_safeattrs(self):
        x = self.conn.root.getlist()
        #self.require(x == [1, 2, 3]) -- can't compare remote objects, sorry
        #self.require(x * 2 == [1, 2, 3, 1, 2, 3])
        self.require([y*2 for y in x] == [2, 4, 6])
    
    def step_context(self):
        with self.conn.root.context(3) as x:
            self.require(x == 20)
        self.require(on_context_exit)
        pass
    
    def step_metaclasses(self):
        x = self.conn.root.getmeta()
        self.log(x)


if __name__ == '__main__':
    CustomService.run()


