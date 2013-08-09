from __future__ import with_statement
import rpyc
import unittest

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


class TestContextManagers(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)

    def tearDown(self):
        self.conn.close()
    
    def test_context(self):
        with self.conn.root.context(3) as x:
            print( "entering test" )
            self.assertTrue(on_context_enter)
            self.assertFalse(on_context_exit)
            print( "got past context enter" )
            self.assertEqual(x, 20)
            print( "got past x=20" )
        self.assertTrue(on_context_exit)
        print( "got past on_context_exit" )


if __name__ == "__main__":
    unittest.main()

