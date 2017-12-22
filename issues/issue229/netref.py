"""
**NetRef**: a transparent *network reference*. This module contains quite a lot
of *magic*, so beware.
"""
import sys
import inspect
import types

import cPickle as pickle
import consts


_local_netref_attrs = frozenset([
    '____conn__', '____oid__', '____refcount__', '__class__', '__cmp__', '__del__', '__delattr__',
    '__dir__', '__doc__', '__getattr__', '__getattribute__', '__hash__',
    '__init__', '__metaclass__', '__module__', '__new__', '__reduce__',
    '__reduce_ex__', '__repr__', '__setattr__', '__slots__', '__str__',
    '__weakref__', '__dict__',
])
"""the set of attributes that are local to the netref object"""

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
    if not conn:
        raise ReferenceError('weakly-referenced object no longer exists')
    oid = object.__getattribute__(proxy, "____oid__")
    return conn.sync_request(handler, oid, *args)


class BaseNetref(object):
    """The base netref class, from which all netref classes derive. Some netref
    classes are "pre-generated" and cached upon importing this module (those
    defined in the :data:`_builtin_types`), and they are shared between all
    connections.

    The rest of the netref classes are created by :meth:`rpyc.core.protocl.Connection._unbox`,
    and are private to the connection.

    Do not use this class directly; use :func:`class_factory` instead.

    :param conn: the :class:`rpyc.core.protocol.Connection` instance
    :param oid: the unique object ID of the remote object
    """
    # this is okay with py3k -- see below
    __slots__ = ["____conn__", "____oid__", "__weakref__", "____refcount__"]
    def __init__(self, conn, oid):
        self.____conn__ = conn
        self.____oid__ = oid
        self.____refcount__ = 1

    def __getattribute__(self, name):
        if name in _local_netref_attrs:
            return object.__getattribute__(self, name)
        elif name == "__call__":                          # IronPython issue #10
            return object.__getattribute__(self, "__call__")
        else:
            return syncreq(self, consts.HANDLE_GETATTR, name)

    def __getattr__(self, name):
        return syncreq(self, consts.HANDLE_GETATTR, name)


def _make_method(name, doc):
    """creates a method with the given name and docstring that invokes
    :func:`syncreq` on its `self` argument"""

    name = str(name)                                      # IronPython issue #10
    if name == "__call__":
        def __call__(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, consts.HANDLE_CALL, args, kwargs)
        return __call__
    else:
        def method(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, consts.HANDLE_CALLATTR, name, args, kwargs)
        method.__name__ = name
        return method

def inspect_methods(obj):
    """introspects the given (local) object, returning a list of all of its
    methods (going up the MRO).

    :param obj: any local (not proxy) python object

    :returns: a list of ``(method name, docstring)`` tuples of all the methods
              of the given object
    """
    methods = {}
    attrs = {}
    if isinstance(obj, type):
        mros = list(reversed(type(obj).__mro__)) + list(reversed(obj.__mro__))
    else:
        mros = reversed(type(obj).__mro__)
    for basecls in mros:
        attrs.update(basecls.__dict__)
    for name, attr in attrs.items():
        if name not in _local_netref_attrs and hasattr(attr, "__call__"):
            methods[name] = inspect.getdoc(attr)
    return methods.items()

def class_factory(clsname, modname, methods):
    """Creates a netref class proxying the given class

    :param clsname: the class's name
    :param modname: the class's module name
    :param methods: a list of ``(method name, docstring)`` tuples, of the methods
                    that the class defines

    :returns: a netref class
    """
    clsname = str(clsname)                                # IronPython issue #10
    modname = str(modname)                                # IronPython issue #10
    ns = {"__slots__" : ()}
    for name, doc in methods:
        name = str(name)                                  # IronPython issue #10
        if name not in _local_netref_attrs:
            ns[name] = _make_method(name, doc)
    ns["__module__"] = modname
    if modname in sys.modules and hasattr(sys.modules[modname], clsname):
        ns["__class__"] = getattr(sys.modules[modname], clsname)
    else:
        # to be resolved by the instance
        ns["__class__"] = None
    return type(clsname, (BaseNetref,), ns)

builtin_classes_cache = {}
"""The cache of built-in netref classes (each of the types listed in
:data:`_builtin_types`). These are shared between all RPyC connections"""


