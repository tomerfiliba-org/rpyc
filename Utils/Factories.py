"""
the factory: 
exposes a nice and easy interface to the internals of rpyc. 
this module, along with Utils, are the only modules most clients will need.
"""
from weakref import WeakValueDictionary
from Serving import DEFAULT_PORT
from Rpyc.Stream import SocketStream, PipeStream
from Rpyc.Channel import Channel
from Rpyc.Connection import Connection
from Rpyc.AsyncNetProxy import AsyncNetProxy


__all__ = ["SocketConnection", "PipeConnection", "SecSocketConnection", "Async", 
    "LoginError"]

#
# connection factories
#
def SocketConnection(host, port = DEFAULT_PORT):
    """shorthand for creating a conneciton over a socket to a server"""
    return Connection(Channel(SocketStream.from_new_socket(host, port)))

def PipeConnection(incoming, outgoing):
    """shorthand for creating a conneciton over a pipe"""
    return Connection(Channel(PipeStream(incoming, outgoing)))

class LoginError(Exception):
    pass

def SecSocketConnection(host, username, password, port = DEFAULT_PORT):
    """shorthand for creating secure socket connections"""
    try:
        stream = SocketStream.from_new_secure_socket(host, port, username, password)
    except:
        raise LoginError("authentication failure")
    return Connection(Channel(stream))

#
# Async factory
#
_async_proxy_cache = WeakValueDictionary()

def Async(proxy):
    """a factory for creating asynchronous proxies for existing synchronous ones"""
    key = id(proxy)
    if key in _async_proxy_cache:
        return _async_proxy_cache[key]
    else:
        new_proxy = AsyncNetProxy(proxy)
        _async_proxy_cache[key] = new_proxy
        return new_proxy




