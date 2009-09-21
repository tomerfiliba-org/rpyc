"""
NetRef - transparent network references implementation.

SURGEON GENERAL'S WARNING: Black magaic is known to causes Lung Cancer,
Heart Disease, Emphysema, and May Complicate Pregnancy. Close your eyes!
"""
import sys
import inspect
import types
import cPickle as pickle
from rpyc.core import consts


_local_netref_attrs = frozenset([
    '____conn__', '____oid__', '__class__', '__cmp__', '__del__', '__delattr__', 
    '__dir__', '__doc__', '__getattr__', '__getattribute__', '__hash__', 
    '__init__', '__metaclass__', '__module__', '__new__', '__reduce__', 
    '__reduce_ex__', '__repr__', '__setattr__', '__slots__', '__str__', 
    '__weakref__', '__dict__', '__members__', '__methods__',
])

_builtin_types = [
    type, object, types.InstanceType, types.ClassType, bool, complex, dict, 
    file, float, int, list, long, slice, str, basestring, tuple, unicode, 
    str, set, frozenset, Exception, types.NoneType, types.DictProxyType, 
    types.BuiltinFunctionType, types.GeneratorType, types.MethodType, 
    types.CodeType, types.FrameType, types.TracebackType, xrange,
    types.ModuleType, types.FunctionType,
    
    type(int.__add__), # wrapper_descriptor
    type((1).__add__), # method-wrapper
    type(iter([])), # listiterator
    type(iter(())), # tupleiterator
    type(iter(xrange(10))), # rangeiterator
    type(iter(set())), # setiterator
]

_normalized_builtin_types = dict(((t.__name__, t.__module__), t) 
    for t in _builtin_types)

def syncreq(proxy, handler, *args):
    """performs a synchronous request on the given proxy object"""
    conn = object.__getattribute__(proxy, "____conn__")
    oid = object.__getattribute__(proxy, "____oid__")
    return conn().sync_request(handler, oid, *args)

def asyncreq(proxy, handler, *args):
    """performs an asynchronous request on the given proxy object, 
    retuning an AsyncResult"""
    conn = object.__getattribute__(proxy, "____conn__")
    oid = object.__getattribute__(proxy, "____oid__")
    return conn().async_request(handler, oid, *args)

class NetrefMetaclass(type):
    """a metaclass just to customize the __repr__ of netref classes"""
    __slots__ = ()
    def __repr__(self):
        if self.__module__:
            return "<netref class '%s.%s'>" % (self.__module__, self.__name__)
        else:
            return "<netref class '%s'>" % (self.__name__,)

class BaseNetref(object):
    """the base netref object, from which all netref classes derive"""
    __metaclass__ = NetrefMetaclass
    __slots__ = ["____conn__", "____oid__", "__weakref__"]
    def __init__(self, conn, oid):
        self.____conn__ = conn
        self.____oid__ =  oid
    def __del__(self):
        try:
            asyncreq(self, consts.HANDLE_DEL)
        except:
            pass
    
    def __getattribute__(self, name):
        if name in _local_netref_attrs:
            if name == "__class__":
                cls = object.__getattribute__(self, "__class__")
                if cls is None:
                    cls = self.__getattr__("__class__")
                return cls
            elif name == "__doc__":
                return self.__getattr__("__doc__")
            elif name == "__members__": # sys.version_info < (2, 6)
                return self.__dir__()
            else:
                return object.__getattribute__(self, name)
        else:
            return syncreq(self, consts.HANDLE_GETATTR, name)
    def __getattr__(self, name):
        return syncreq(self, consts.HANDLE_GETATTR, name)
    def __delattr__(self, name):
        if name in _local_netref_attrs:
            object.__delattr__(self, name)
        else:
            syncreq(self, consts.HANDLE_DELATTR, name)
    def __setattr__(self, name, value):
        if name in _local_netref_attrs:
            object.__setattr__(self, name, value)
        else:
            syncreq(self, consts.HANDLE_SETATTR, name, value)
    def __dir__(self):
        return list(syncreq(self, consts.HANDLE_DIR))
    
    # support for metaclasses
    def __hash__(self):
        return syncreq(self, consts.HANDLE_HASH)
    def __cmp__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other)
    def __repr__(self):
        return syncreq(self, consts.HANDLE_REPR)
    def __str__(self):
        return syncreq(self, consts.HANDLE_STR)
    # support for pickle
    def __reduce_ex__(self, proto):
        return pickle.loads, (syncreq(self, consts.HANDLE_PICKLE, proto),)

def _make_method(name, doc):
    if name == "__call__":
        def __call__(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, consts.HANDLE_CALL, args, kwargs)
        __call__.__doc__ = doc
        return __call__
    else:
        def method(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, consts.HANDLE_CALLATTR, name, args, kwargs)
        method.__name__ = name
        method.__doc__ = doc
        return method

def inspect_methods(obj):
    """returns a list of (method name, docstring) tuples of all the methods of 
    the given object"""
    methods = {}
    attrs = {}
    if isinstance(obj, type):
        # don't forget the darn metaclass
        mros = list(reversed(type(obj).__mro__)) + list(reversed(obj.__mro__)) 
    else:
        mros = reversed(type(obj).__mro__)
    for basecls in mros:
        attrs.update(basecls.__dict__)
    for name, attr in attrs.iteritems():
        if name not in _local_netref_attrs and hasattr(attr, "__call__"):
            methods[name] = inspect.getdoc(attr)
    return methods.items()

def class_factory(clsname, modname, methods):
    ns = {"__slots__" : ()}
    for name, doc in methods:
        if name not in _local_netref_attrs:
            ns[name] = _make_method(name, doc)
    ns["__module__"] = modname
    if modname in sys.modules and hasattr(sys.modules[modname], clsname):
        ns["__class__"] = getattr(sys.modules[modname], clsname)
    elif (clsname, modname) in _normalized_builtin_types:
        ns["__class__"] = _normalized_builtin_types[clsname, modname]
    else:
        ns["__class__"] = None # to be resolved by the instance
    return type(clsname, (BaseNetref,), ns)

builtin_classes_cache = {}
for cls in _builtin_types:
    builtin_classes_cache[cls.__name__, cls.__module__] = class_factory(
        cls.__name__, cls.__module__, inspect_methods(cls))


