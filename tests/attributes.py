from testbase import TestBase
import rpyc


class Properties(object):
    def __init__(self):
        self._x = 0
    
    @property
    def counter(self):
        self._x += 1
        return self._x
    
    @property
    def dont_touch_me(self):
        # reconstruct bug reported by Andrew Stromnov
        # http://groups.google.com/group/rpyc/msg/aa6110259481f194
        1/0


class AttributeTest(TestBase):
    def setup(self):
        self.conn = rpyc.classic.connect_thread()
    
    def cleanup(self):
        self.conn.close()
    
    def step_properties(self):
        p = self.conn.modules["attributes"].Properties()
        self.log(p.counter) # 1
        self.log(p.counter) # 2
        self.log(p.counter) # 3
        self.require(p.counter == 4) # 4


    
if __name__ == "__main__":
    AttributeTest.run()

