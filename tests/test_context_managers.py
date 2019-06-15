from __future__ import with_statement
import rpyc
import unittest

from contextlib import contextmanager


class MyService(rpyc.Service):

    on_context_enter = False
    on_context_exit = False
    on_context_exc = False

    @contextmanager
    def exposed_context(self, y):
        self.on_context_enter = True
        try:
            yield 17 + y
        except Exception:
            self.on_context_exc = True
            raise
        finally:
            self.on_context_exit = True


class TestContextManagers(unittest.TestCase):
    def setUp(self):
        self.service = MyService()
        self.conn = rpyc.connect_thread(remote_service=self.service)

    def tearDown(self):
        self.conn.close()

    def test_context(self):
        service = self.service
        with self.conn.root.context(3) as x:
            self.assertTrue(service.on_context_enter)
            self.assertFalse(service.on_context_exc)
            self.assertFalse(service.on_context_exit)
            self.assertEqual(x, 20)
        self.assertFalse(service.on_context_exc)
        self.assertTrue(service.on_context_exit)

    def test_context_exception(self):
        class MyException(Exception):
            pass

        service = self.service

        def use_context():
            with self.conn.root.context(3):
                self.assertTrue(service.on_context_enter)
                self.assertFalse(service.on_context_exc)
                self.assertFalse(service.on_context_exit)
                raise MyException()

        self.assertRaises(MyException, use_context)

        self.assertTrue(service.on_context_exc)
        self.assertTrue(service.on_context_exit)


if __name__ == "__main__":
    unittest.main()
