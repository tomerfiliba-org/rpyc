"""*NetRef*: a transparent *network reference*. This module contains quite a lot
of *magic*, so beware.
"""
import sys
import types
from rpyc.lib import get_methods, get_id_pack
from rpyc.lib.compat import pickle, is_py3k, maxint, with_metaclass
from rpyc.core import consts


builtin_id_pack_cache = {}  # name_pack -> id_pack
builtin_classes_cache = {}  # id_pack -> class
# If these can be accessed, numpy will try to load the array from local memory,
# resulting in exceptions and/or segfaults, see #236:
DELETED_ATTRS = frozenset([
    '__array_struct__', '__array_interface__',
])

LOCAL_ATTRS = frozenset([
    '____conn__', '____id_pack__', '____refcount__', '__class__', '__cmp__', '__del__', '__delattr__',
    '__dir__', '__doc__', '__getattr__', '__getattribute__', '__hash__', '__instancecheck__',
    '__init__', '__metaclass__', '__module__', '__new__', '__reduce__',
    '__reduce_ex__', '__repr__', '__setattr__', '__slots__', '__str__',
    '__weakref__', '__dict__', '__methods__', '__exit__',
    '__eq__', '__ne__', '__lt__', '__gt__', '__le__', '__ge__',
]) | DELETED_ATTRS
"""the set of attributes that are local to the netref object"""

_builtin_types = [
    type, object, bool, complex, dict, float, int, list, slice, str, tuple, set,
    frozenset, Exception, type(None), types.BuiltinFunctionType, types.GeneratorType,
    types.MethodType, types.CodeType, types.FrameType, types.TracebackType,
    types.ModuleType, types.FunctionType,

    type(int.__add__),      # wrapper_descriptor
    type((1).__add__),      # method-wrapper
    type(iter([])),         # listiterator
    type(iter(())),         # tupleiterator
    type(iter(set())),      # setiterator
]
"""a list of types considered built-in (shared between connections)"""

try:
    BaseException
except NameError:
    pass
else:
    _builtin_types.append(BaseException)

if is_py3k:
    _builtin_types.extend([
        bytes, bytearray, type(iter(range(10))), memoryview,
    ])
    xrange = range
else:
    _builtin_types.extend([
        basestring, unicode, long, xrange, type(iter(xrange(10))), file,  # noqa
        types.InstanceType, types.ClassType, types.DictProxyType,
    ])
_normalized_builtin_types = {}


def syncreq(proxy, handler, *args):
    """Performs a synchronous request on the given proxy object.
    Not intended to be invoked directly.

    :param proxy: the proxy on which to issue the request
    :param handler: the request handler (one of the ``HANDLE_XXX`` members of
                    ``rpyc.protocol.consts``)
    :param args: arguments to the handler

    :raises: any exception raised by the operation will be raised
    :returns: the result of the operation
    """
    conn = object.__getattribute__(proxy, "____conn__")
    return conn.sync_request(handler, proxy, *args)


def asyncreq(proxy, handler, *args):
    """Performs an asynchronous request on the given proxy object.
    Not intended to be invoked directly.

    :param proxy: the proxy on which to issue the request
    :param handler: the request handler (one of the ``HANDLE_XXX`` members of
                    ``rpyc.protocol.consts``)
    :param args: arguments to the handler

    :returns: an :class:`~rpyc.core.async_.AsyncResult` representing
              the operation
    """
    conn = object.__getattribute__(proxy, "____conn__")
    return conn.async_request(handler, proxy, *args)


class NetrefMetaclass(type):
    """A *metaclass* used to customize the ``__repr__`` of ``netref`` classes.
    It is quite useless, but it makes debugging and interactive programming
    easier"""

    __slots__ = ()

    def __repr__(self):
        if self.__module__:
            return "<netref class '%s.%s'>" % (self.__module__, self.__name__)
        else:
            return "<netref class '%s'>" % (self.__name__,)


class BaseNetref(with_metaclass(NetrefMetaclass, object)):
    """The base netref class, from which all netref classes derive. Some netref
    classes are "pre-generated" and cached upon importing this module (those
    defined in the :data:`_builtin_types`), and they are shared between all
    connections.

    The rest of the netref classes are created by :meth:`rpyc.core.protocl.Connection._unbox`,
    and are private to the connection.

    Do not use this class directly; use :func:`class_factory` instead.

    :param conn: the :class:`rpyc.core.protocol.Connection` instance
    :param id_pack: id tuple for an object ~ (name_pack, remote-class-id, remote-instance-id)
        (cont.) name_pack := __module__.__name__ (hits or misses on builtin cache and sys.module)
                remote-class-id := id of object class (hits or misses on netref classes cache and instance checks)
                remote-instance-id := id object instance (hits or misses on proxy cache)
        id_pack is usually created by rpyc.lib.get_id_pack
    """
    __slots__ = ["____conn__", "____id_pack__", "__weakref__", "____refcount__"]

    def __init__(self, conn, id_pack):
        self.____conn__ = conn
        self.____id_pack__ = id_pack
        self.____refcount__ = 1

    def __del__(self):
        try:
            asyncreq(self, consts.HANDLE_DEL, self.____refcount__)
        except Exception:
            # raised in a destructor, most likely on program termination,
            # when the connection might have already been closed.
            # it's safe to ignore all exceptions here
            pass

    def __getattribute__(self, name):
        if name in LOCAL_ATTRS:
            if name == "__class__":
                cls = object.__getattribute__(self, "__class__")
                if cls is None:
                    cls = self.__getattr__("__class__")
                return cls
            elif name == "__doc__":
                return self.__getattr__("__doc__")
            elif name in DELETED_ATTRS:
                raise AttributeError()
            else:
                return object.__getattribute__(self, name)
        elif name == "__call__":                          # IronPython issue #10
            return object.__getattribute__(self, "__call__")
        elif name == "__array__":
            return object.__getattribute__(self, "__array__")
        else:
            return syncreq(self, consts.HANDLE_GETATTR, name)

    def __getattr__(self, name):
        if name in DELETED_ATTRS:
            raise AttributeError()
        return syncreq(self, consts.HANDLE_GETATTR, name)

    def __delattr__(self, name):
        if name in LOCAL_ATTRS:
            object.__delattr__(self, name)
        else:
            syncreq(self, consts.HANDLE_DELATTR, name)

    def __setattr__(self, name, value):
        if name in LOCAL_ATTRS:
            object.__setattr__(self, name, value)
        else:
            syncreq(self, consts.HANDLE_SETATTR, name, value)

    def __dir__(self):
        return list(syncreq(self, consts.HANDLE_DIR))

    # support for metaclasses
    def __hash__(self):
        return syncreq(self, consts.HANDLE_HASH)

    def __cmp__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__cmp__')

    def __eq__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__eq__')

    def __ne__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__ne__')

    def __lt__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__lt__')

    def __gt__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__gt__')

    def __le__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__le__')

    def __ge__(self, other):
        return syncreq(self, consts.HANDLE_CMP, other, '__ge__')

    def __repr__(self):
        return syncreq(self, consts.HANDLE_REPR)

    def __str__(self):
        return syncreq(self, consts.HANDLE_STR)

    def __exit__(self, exc, typ, tb):
        return syncreq(self, consts.HANDLE_CTXEXIT, exc)  # can't pass type nor traceback

    def __reduce_ex__(self, proto):
        # support for pickling netrefs
        return pickle.loads, (syncreq(self, consts.HANDLE_PICKLE, proto),)

    def __instancecheck__(self, other):
        # support for checking cached instances across connections
        if isinstance(other, BaseNetref):
            if self.____id_pack__[2] != 0:
                raise TypeError("isinstance() arg 2 must be a class, type, or tuple of classes and types")
            elif self.____id_pack__[1] == other.____id_pack__[1]:
                if other.____id_pack__[2] == 0:
                    return False
                elif other.____id_pack__[2] != 0:
                    return True
            else:
                return syncreq(self, consts.HANDLE_INSTANCECHECK, other.____id_pack__)
        else:
            return isinstance(other, self.__class__)


def _make_method(name, doc):
    """creates a method with the given name and docstring that invokes
    :func:`syncreq` on its `self` argument"""

    slicers = {"__getslice__": "__getitem__", "__delslice__": "__delitem__", "__setslice__": "__setitem__"}

    name = str(name)                                      # IronPython issue #10
    if name == "__call__":
        def __call__(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, consts.HANDLE_CALL, args, kwargs)
        __call__.__doc__ = doc
        return __call__
    elif name in slicers:                                 # 32/64 bit issue #41
        def method(self, start, stop, *args):
            if stop == maxint:
                stop = None
            return syncreq(self, consts.HANDLE_OLDSLICING, slicers[name], name, start, stop, args)
        method.__name__ = name
        method.__doc__ = doc
        return method
    elif name == "__array__":
        def __array__(self):
            # Note that protocol=-1 will only work between python
            # interpreters of the same version.
            return pickle.loads(syncreq(self, consts.HANDLE_PICKLE, -1))
        __array__.__doc__ = doc
        return __array__
    else:
        def method(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, consts.HANDLE_CALLATTR, name, args, kwargs)
        method.__name__ = name
        method.__doc__ = doc
        return method


def class_factory(id_pack, methods):
    """Creates a netref class proxying the given class

    :param id_pack: the id pack used for proxy communication
    :param methods: a list of ``(method name, docstring)`` tuples, of the methods that the class defines

    :returns: a netref class
    """
    ns = {"__slots__": (), "__class__": None}
    name_pack = id_pack[0]
    if name_pack is not None:  # attempt to resolve against builtins and sys.modules
        ns["__class__"] = _normalized_builtin_types.get(name_pack)
        if ns["__class__"] is None:
            _module = None
            didx = name_pack.rfind('.')
            if didx != -1:
                _module = sys.modules.get(name_pack[:didx])
                if _module is not None:
                    _module = getattr(_module, name_pack[didx + 1:], None)
                else:
                    _module = sys.modules.get(name_pack)
            else:
                _module = sys.modules.get(name_pack)
            if _module:
                if id_pack[2] == 0:
                    ns["__class__"] = _module
                else:
                    ns["__class__"] = getattr(_module, "__class__", None)

    for name, doc in methods:
        name = str(name)  # IronPython issue #10
        if name not in LOCAL_ATTRS:  # i.e. `name != __class__`
            ns[name] = _make_method(name, doc)
    return type(name_pack, (BaseNetref,), ns)


for _builtin in _builtin_types:
    _id_pack = get_id_pack(_builtin)
    _name_pack = _id_pack[0]
    _normalized_builtin_types[_name_pack] = _builtin
    _builtin_methods = get_methods(LOCAL_ATTRS, _builtin)
    # assume all normalized builtins are classes
    builtin_classes_cache[_name_pack] = class_factory(_id_pack, _builtin_methods)
