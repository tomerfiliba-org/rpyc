"""
helpers and wrappers for common rpyc tasks
"""
import threading
from rpyc.utils.lib import WeakValueDict, callable
from rpyc.core.consts import HANDLE_BUFFITER, HANDLE_CALL
from rpyc.core.netref import BaseNetref, syncreq, asyncreq


def buffiter(obj, chunk = 10, max_chunk = 1000, factor = 2):
    """buffering iterator - reads the remote iterator in chunks starting with
    `chunk` up to `max_chunk`, multiplying by `factor` as an exponential 
    backoff"""
    if factor < 1:
        raise ValueError("factor must be >= 1, got %r" % (factor,))
    it = iter(obj)
    count = chunk
    while True:
        items = syncreq(it, HANDLE_BUFFITER, count)
        count = min(count * factor, max_chunk)
        if not items:
            break
        for elem in items:
            yield elem

class _Async(object):
    """creates an async proxy wrapper over an existing proxy. async proxies 
    are cached. invoking an async proxy will return an AsyncResult instead of
    blocking"""
    
    __slots__ = ("proxy", "__weakref__")
    def __init__(self, proxy):
        self.proxy = proxy
    def __call__(self, *args, **kwargs):
        return asyncreq(self.proxy, HANDLE_CALL, args, tuple(kwargs.items()))
    def __repr__(self):
        return "async(%r)" % (self.proxy,)

_async_proxies_cache = WeakValueDict()
def async(proxy):
    pid = id(proxy)
    if pid in _async_proxies_cache:
        return _async_proxies_cache[pid]
    if not hasattr(proxy, "____conn__") or not hasattr(proxy, "____oid__"):
        raise TypeError("'proxy' must be a Netref: %r", (proxy,))
    if not callable(proxy):
        raise TypeError("'proxy' must be callable: %r" % (proxy,))
    caller = _Async(proxy)
    _async_proxies_cache[id(caller)] = _async_proxies_cache[pid] = caller
    return caller

async.__doc__ = _Async.__doc__

class timed(object):
    """creates a timed asynchronous proxy. invoking the timed proxy will
    run in the background and will raise an AsyncResultTimeout exception
    if the computation does not terminate within the given timeout"""
    
    __slots__ = ("__weakref__", "proxy", "timeout")
    def __init__(self, proxy, timeout):
        self.proxy = async(proxy)
        self.timeout = timeout
    def __call__(self, *args, **kwargs):
        res = self.proxy(*args, **kwargs)
        res.set_expiry(self.timeout)
        return res
    def __repr__(self):
        return "timed(%r, %r)" % (self.proxy.proxy, self.timeout)

class BgServingThread(object):
    """runs an RPyC server in the background to serve all requests and replies
    that arrive on the given RPyC connection. the thread is created along with
    the object; you can use the stop() method to stop the server thread"""
    INTERVAL = 0.1
    def __init__(self, conn):
        self._conn = conn
        self._thread = threading.Thread(target = self._bg_server)
        self._thread.setDaemon(True)
        self._active = True
        self._thread.start()
    def __del__(self):
        if self._active:
            self.stop()
    def _bg_server(self):
        try:
            while self._active:
                self._conn.serve(self.INTERVAL)
        except Exception:
            if self._active:
                raise
    def stop(self):
        """stop the server thread. once stopped, it cannot be resumed. you will
        have to create a new BgServingThread object later.""" 
        self._active = False
        self._thread.join()
        self._conn = None





