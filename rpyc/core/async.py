import time


class AsyncResultTimeout(Exception):
    pass

class AsyncResult(object):
    """AsyncResult is an object that represent a computation that occurs in 
    the background and will eventually have a result. Use the .value property
    to access the result (which will block if the result has not yet arrived)
    """
    __slots__ = ["_conn", "_is_ready", "_is_exc", "_callbacks", "_obj", "_ttl"]
    def __init__(self, conn):
        self._conn = conn
        self._is_ready = False
        self._is_exc = None
        self._obj = None
        self._callbacks = []
        self._ttl = None
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
        self._is_ready = True
        self._is_exc = is_exc
        self._obj = obj
        for cb in self._callbacks:
            cb(self)
        del self._callbacks[:]
    
    def wait(self):
        """wait for the result to arrive. if the AsyncResult object has an
        expiry set, and the result does not arrive within that timeout,
        an AsyncResultTimeout exception is raised"""
        if self._is_ready:
            return
        if self._ttl is None:
            while not self._is_ready:
                self._conn.serve()
        else:
            while True:
                timeout = self._ttl - time.time()
                self._conn.poll(timeout = max(timeout, 0))
                if self._is_ready:
                    break
                if timeout <= 0:
                    raise AsyncResultTimeout("result expired")
    def add_callback(self, func):
        """adds a callback to be invoked when the result arrives. the 
        callback function takes a single argument, which is the current 
        AsyncResult (self)"""
        if self._is_ready:
            func(self)
        else:
            self._callbacks.append(func)
    def set_expiry(self, timeout):
        """set the expiry time (in seconds, relative to now) or None for 
        unlimited time"""
        if timeout is None:
            self._ttl = None
        else:
            self._ttl = time.time() + timeout
    
    @property
    def ready(self):
        """a predicate of whether the result has arrived"""
        if self.expired:
            return False
        if not self._is_ready:
            self._conn.poll_all()
        return self._is_ready
    @property
    def error(self):
        """a predicate of whether the returned result is an exception"""
        if self.ready:
            return self._is_exc
        return False
    @property
    def expired(self):
        """a predicate of whether the async result has expired"""
        if self._is_ready or self._ttl is None:
            return False
        else:
            return time.time() > self._ttl

    @property
    def value(self):
        """returns the result of the operation. if the result has not yet 
        arrived, accessing this property will wait for it. if the result does
        not arrive before the expiry time elapses, AsyncResultTimeout is 
        raised. if the returned result is an exception, it will be raised here.
        otherwise, the result is returned directly."""
        self.wait()
        if self._is_exc:
            raise self._obj
        else:
            return self._obj



