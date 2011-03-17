from __future__ import with_statement
from contextlib import contextmanager

import rpyc


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


class Test_Python25(object):
    def setup(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)
    
    def teardown(self):
        self.conn.close()
    
    def test_context(self):
        with self.conn.root.context(3) as x:
            print( "entering test" )
            assert on_context_enter
            print( "got past context enter" )
            assert x == 20
            print( "got past x=20" )
        assert on_context_exit
        print( "got past on_context_exit" ) 
