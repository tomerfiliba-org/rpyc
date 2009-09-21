from NetProxy import NetProxyWrapper, _get_conn, _get_oid
from Lib import raise_exception


class AsyncNetProxy(NetProxyWrapper):
    """wraps an exiting synchronous netproxy to make is asynchronous 
    (remote operations return AsyncResult objects)"""
    __slots__ = []

    def __request__(self, handler, *args):
        res = AsyncResult(_get_conn(self))
        _get_conn(self).async_request(res.callback, handler, _get_oid(self), *args)
        return res

    # must return a string... and it's not meaningful to return the repr of an async result
    def __repr__(self, *args):
        return self.__request__("handle_repr", *args).result
    def __str__(self, *args):
        return self.__request__("handle_str", *args).result      


class AsyncResult(object):
    """represents the result of an asynchronous operation"""
    STATE_PENDING = "pending"
    STATE_READY = "ready"
    STATE_EXCEPTION = "exception"
    __slots__ = ["conn", "_state", "_result", "_on_ready"]
    
    def __init__(self, conn):
        self.conn = conn
        self._state = self.STATE_PENDING
        self._result = None
        self._on_ready = None
    
    def __repr__(self):
        return "<AsyncResult (%s) at 0x%08x>" % (self._state, id(self))
    
    def callback(self, obj, is_exception):
        self._result = obj
        if is_exception:
            self._state = self.STATE_EXCEPTION
        else:
            self._state = self.STATE_READY
        if self._on_ready is not None:
            self._on_ready(self)
    
    def _get_on_ready(self):
        return self._ready_callback

    def _set_on_ready(self, obj):
        self._on_ready = obj
        if self._state != self.STATE_PENDING:
            self._on_ready(self)
    
    def _get_is_ready(self):
        if self._state == self.STATE_PENDING:
            self.conn.poll()
        return self._state != self.STATE_PENDING
    
    def _get_result(self):
        while self._state == self.STATE_PENDING:
            self.conn.serve()
        if self._state == self.STATE_READY:
            return self._result
        elif self._state == self.STATE_EXCEPTION:
            raise_exception(*self._result)
    
    is_ready = property(_get_is_ready, 
        doc = "indicates whether or not the result is ready")
    result = property(_get_result, 
        doc = "the value of the async result (may block)")
    on_ready = property(_get_on_ready, _set_on_ready, 
        doc = "if not None, specifies a callback which is called when the result is ready")












