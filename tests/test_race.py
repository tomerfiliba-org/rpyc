import rpyc
import rpyc.core as rc
import rpyc.core.async_ as rc_async_
import rpyc.core.protocol as rc_protocol
import contextlib
import signal
import threading
import time
import unittest


class TestRace(unittest.TestCase):
    def setUp(self):
        self.connection = rpyc.classic.connect_thread()

        self.a_str = rpyc.async_(self.connection.builtin.str)

    def tearDown(self):
        self.connection.close()

    def test_asyncresult_race(self):
        with _patch():
            def hook():
                time.sleep(0.2)  # loose race

            _AsyncResult._HOOK = hook

            threading.Thread(target=self.connection.serve_all).start()
            time.sleep(0.1)  # wait for thread to serve

            # schedule KeyboardInterrupt
            thread_id = threading.get_ident()
            _ = lambda: signal.pthread_kill(thread_id, signal.SIGINT)
            timer = threading.Timer(1, _)
            timer.start()

            a_result = self.a_str("")  # request
            time.sleep(0.1)  # wait for race to start
            try:
                a_result.wait()
            except KeyboardInterrupt:
                raise Exception("deadlock")

            timer.cancel()


class _AsyncResult(rc_async_.AsyncResult):
    _HOOK = None

    def __call__(self, *args, **kwargs):
        hook = type(self)._HOOK
        if hook is not None:
            hook()
        return super().__call__(*args, **kwargs)


@contextlib.contextmanager
def _patch():
    AsyncResult = rc_async_.AsyncResult
    try:
        rc_async_.AsyncResult = _AsyncResult
        rc_protocol.AsyncResult = _AsyncResult  # from import
        rc.AsyncResult = _AsyncResult  # from import
        rpyc.AsyncResult = _AsyncResult  # from import
        yield

    finally:
        rc_async_.AsyncResult = AsyncResult
        rc_protocol.AsyncResult = AsyncResult
        rc.AsyncResult = AsyncResult
        rpyc.AsyncResult = AsyncResult


if __name__ == "__main__":
    unittest.main()
