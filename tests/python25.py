from __future__ import with_statement
from testbase import TestBase
import rpyc
from contextlib import contextmanager


on_context_enter = False
on_context_exit = False

class MyService(rpyc.Service):
    @contextmanager
    def exposed_context(self, y):
        global on_context_enter, on_context_exit
        on_context_enter = True
        try:
            yield 17 + y
        finally:
            on_context_exit = True

class Python25Test(TestBase):
    def setup(self):
        self.conn = rpyc.connect_thread(remote_service = MyService)
    
    def cleanup(self):
        self.conn.close()
    
    def step_context(self):
        with self.conn.root.context(3) as x:
            self.require(on_context_enter)
            self.require(x == 20)
        self.require(on_context_exit)


if __name__ == "__main__":
    Python25Test.run()




