from __future__ import with_statement
import rpyc
import unittest

from contextlib import contextmanager


class MyService(rpyc.Service):

    def exposed_reset(self):
        global on_context_enter, on_context_exit, on_context_exc
        on_context_enter = False
        on_context_exit = False
        on_context_exc = False

    @contextmanager
    def exposed_context(self, y):
        global on_context_enter, on_context_exit, on_context_exc
        on_context_enter = True
        try:
            yield 17 + y
        except:
            on_context_exc = True
            raise
        finally:
            on_context_exit = True


class TestContextManagers(unittest.TestCase):
    def setUp(self):
        self.conn = rpyc.connect_thread(remote_service=MyService)
        self.conn.root.reset()

    def tearDown(self):
        self.conn.close()

    def test_context(self):
        with self.conn.root.context(3) as x:
            print( "entering test" )
            self.assertTrue(on_context_enter)
            self.assertFalse(on_context_exc)
            self.assertFalse(on_context_exit)
            print( "got past context enter" )
            self.assertEqual(x, 20)
            print( "got past x=20" )
        self.assertFalse(on_context_exc)
        self.assertTrue(on_context_exit)
        print( "got past on_context_exit" )

    def test_context_exception(self):
        class MyException(Exception):
            pass

        with self.assertRaises(MyException):
            with self.conn.root.context(3):
                self.assertTrue(on_context_enter)
                self.assertFalse(on_context_exc)
                self.assertFalse(on_context_exit)
                raise MyException()

        self.assertTrue(on_context_exc)
        self.assertTrue(on_context_exit)

if __name__ == "__main__":
    unittest.main()

