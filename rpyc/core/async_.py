import time
from rpyc.lib import Timeout
from rpyc.lib.compat import TimeoutError as AsyncResultTimeout


class AsyncResult(object):
    """*AsyncResult* represents a computation that occurs in the background and
    will eventually have a result. Use the :attr:`value` property to access the
    result (which will block if the result has not yet arrived).
    """
    __slots__ = ["_conn", "_is_ready", "_is_exc", "_callbacks", "_obj", "_ttl"]
    def __init__(self, conn):
        self._conn = conn
        self._is_ready = False
        self._is_exc = None
        self._obj = None
        self._callbacks = []
        self._ttl = Timeout(None)
    def __repr__(self):
        if self._is_ready:
            state = "ready"
        elif self._is_exc:
            state = "error"
        elif self.expired:
            state = "expired"
        else:
            state = "pending"
        return "<AsyncResult object (%s) at 0x%08x>" % (state, id(self))

    def __call__(self, is_exc, obj):
        if self.expired:
            return
        self._is_exc = is_exc
        self._obj = obj
        self._is_ready = True
        for cb in self._callbacks:
            cb(self)
        del self._callbacks[:]

    def wait(self):
        """Waits for the result to arrive. If the AsyncResult object has an
        expiry set, and the result did not arrive within that timeout,
        an :class:`AsyncResultTimeout` exception is raised"""
        while not self._is_ready and not self._ttl.expired():
            self._conn.serve(self._ttl)
        if not self._is_ready:
            raise AsyncResultTimeout("result expired")

    def add_callback(self, func):
        """Adds a callback to be invoked when the result arrives. The callback
        function takes a single argument, which is the current AsyncResult
        (``self``). If the result has already arrived, the function is invoked
        immediately.

        :param func: the callback function to add
        """
        if self._is_ready:
            func(self)
        else:
            self._callbacks.append(func)
    def set_expiry(self, timeout):
        """Sets the expiry time (in seconds, relative to now) or ``None`` for
        unlimited time

        :param timeout: the expiry time in seconds or ``None``
        """
        self._ttl = Timeout(timeout)

    @property
    def ready(self):
        """Indicates whether the result has arrived"""
        if self._is_ready:
            return True
        if self._ttl.expired():
            return False
        self._conn.poll_all()
        return self._is_ready
    @property
    def error(self):
        """Indicates whether the returned result is an exception"""
        return self.ready and self._is_exc
    @property
    def expired(self):
        """Indicates whether the AsyncResult has expired"""
        return not self._is_ready and self._ttl.expired()

    @property
    def value(self):
        """Returns the result of the operation. If the result has not yet
        arrived, accessing this property will wait for it. If the result does
        not arrive before the expiry time elapses, :class:`AsyncResultTimeout`
        is raised. If the returned result is an exception, it will be raised
        here. Otherwise, the result is returned directly.
        """
        self.wait()
        if self._is_exc:
            raise self._obj
        else:
            return self._obj
