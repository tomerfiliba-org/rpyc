from Lib import ImmDict


class FullyDynamicMetaclass(type):
    """
    a meta class that enables special methods to be accessed like regular names 
    (via __getattr__), like it used to be in old-style classes.
    """

    def __new__(cls, name, bases, namespace):
        special_methods = [
            "__hash__", "__len__", "__iter__", "next", "__reversed__",
            "__add__", "__iadd__", "__radd__", "__sub__", "__isub__", "__rsub__",
            "__mul__", "__imul__", "__rmul__", "__div__", "__idiv__", "__rdiv__", 
            "__truediv__", "__itruediv__", "__rtruediv__", "__floordiv__", 
            "__ifloordiv__", "__rfloorfiv__", "__pow__", "__ipow__", "__rpow__", 
            "__lshift__", "__ilshift__", "__rlshift__", "__rshift__", "__irshift__",
            "__rrshift__", "__and__", "__iand__", "__rand__", "__or__", "__ior__", 
            "__ror__", "__xor__", "__ixor__", "__rxor__", "__mod__", "__imod__", 
            "__rmod__", "__divmod__", "__idivmod__", "__rdivmod__", "__pos__", 
            "__neg__", "__int__", "__float__", "__long__", "__oct__", "__hex__", "__coerce__", 
            "__eq__", "__ne__", "__le__", "__ge__", "__lt__", "__gt__", "__cmp__",
        ]

        def make_method(name):
            def method(self, *a, **k):
                return self.__getattr__(name)(*a, **k)
            return method
    
        special_attributes = ["__doc__", "__module__", "__file__", "__name__"]
    
        def make_property(name):
            def getter(self):
                return self.__getattr__(name)
            def setter(self, value):
                self.__setattr__(name, value)
            def deller(self):
                self.__delattr__(name)
            return property(getter, setter, deller)
    
        for sm in special_methods:
            namespace[sm] = make_method(sm)
        for sa in special_attributes:
            namespace[sa] = make_property(sa)
        return type.__new__(cls, name, bases, namespace)

def _get_conn(proxy):
    return object.__getattribute__(proxy, "____conn__")
def _get_oid(proxy):
    return object.__getattribute__(proxy, "____oid__")

class NetProxy(object):
    """NetProxy - convey local operations to the remote object. this is an abstract class"""
    __metaclass__ = FullyDynamicMetaclass
    __slots__ = ["____conn__", "____oid__", "__weakref__"]
    
    def __init__(self, conn, oid):
        object.__setattr__(self, "____conn__", conn)
        object.__setattr__(self, "____oid__", oid)

    def __request__(self, handler, *args):
        raise NotImplementedError()

    def __call__(self, *args, **kwargs):
        return self.__request__("handle_call", args, ImmDict(kwargs))

    def __delattr__(self, *args):
        return self.__request__("handle_delattr", *args)
    def __getattr__(self, *args):
        return self.__request__("handle_getattr", *args)
    def __setattr__(self, *args):
        return self.__request__("handle_setattr", *args)
    
    def __delitem__(self, *args):
        return self.__request__("handle_delitem", *args)
    def __getitem__(self, *args):
        return self.__request__("handle_getitem", *args)
    def __setitem__(self, *args):
        return self.__request__("handle_setitem", *args)
    
    def __repr__(self, *args):
        return self.__request__("handle_repr", *args)
    def __str__(self, *args):
        return self.__request__("handle_str", *args)
    def __nonzero__(self, *args):
        return self.__request__("handle_bool", *args)

class NetProxyWrapper(NetProxy):
    """a netproxy that wraps an inner netproxy"""
    __slots__ = ["____original__"]

    def __init__(self, proxy):
        NetProxy.__init__(self, _get_conn(proxy), _get_oid(proxy))
        object.__setattr__(self, "____original__", proxy)

def _dummy_callback(*args, **kw):
    pass

class SyncNetProxy(NetProxy):
    """the default, synchronous netproxy"""
    __slots__ = []

    def __del__(self):
        # decref'ing is done asynchronously, because we dont need to wait for the remote 
        # object to die. moreover, we dont care if it fails, because that would mean the 
        # connection is broken, so the remote object is already dead
        try:
            _get_conn(self).async_request(_dummy_callback, "handle_decref", _get_oid(self))
        except:
            pass
    
    def __request__(self, handler, *args):
        return _get_conn(self).sync_request(handler, _get_oid(self), *args)




