"""
replacements for the builtin functions, so they operate correctly on NetProxies
"""
import sys
import inspect
from Rpyc.NetProxy import NetProxy, _get_conn
from Rpyc.Lib import (
    orig_isinstance,
    orig_issubclass,
    orig_dir,
    orig_getattr,
    orig_reload,
    orig_help,
    orig_type)


__all__ = ["dir", "getattr", "hasattr", "reload", "help", "isinstance", "issubclass"]

def dir(*obj):
    """a version of dir() that supports NetProxies"""
    if not obj:
        return sorted(inspect.stack()[1][0].f_locals.keys())
    if not len(obj) == 1:
        raise TypeError("dir expected at most 1 arguments, got %d" % (len(obj),))
    obj = obj[0]
    if orig_isinstance(obj, NetProxy):
        return _get_conn(obj).modules.__builtin__.dir(obj)
    else:
        return orig_dir(obj)

def getattr(obj, name, *default):
    """a version of getattr() that supports NetProxies"""
    if len(default) > 1:
        raise TypeError("getattr expected at most 3 arguments, got %d" % (2 + len(default),))
    if orig_isinstance(obj, NetProxy):
        try:
            return obj.__getattr__(name)
        except AttributeError:
            if not default:
                raise
            return default[0]
    else:
        return orig_getattr(obj, name, *default)

def hasattr(obj, name):
    """a version of hasattr() that supports NetProxies"""
    try:
        getattr(obj, name)
    except AttributeError:
        return False
    else:
        return True

def _get_fullname(cls):
    """
    a heuristic to generate a unique identifier for classes, that is not 
    machine-, platform-, or runtime-dependent
    """
    if orig_isinstance(cls, NetProxy):
        modules = _get_conn(cls).modules.sys.modules
    else:
        modules = sys.modules
    try:
        filename = modules[cls.__module__].__file__
    except (KeyError, AttributeError):
        filename = cls.__module__
    return (filename, cls.__name__)

def _recursive_issubclass(cls, fullname):
    for base in cls.__bases__:
        if _get_fullname(base) == fullname:
            return True
        if _recursive_issubclass(base, fullname):
            return True
    return False

def _remote_issubclass(cls, bases):
    cls_fullname = _get_fullname(cls)
    for base in bases:
        base_fullname = _get_fullname(base)
        if cls_fullname == base_fullname:
            return True
        if _recursive_issubclass(cls, base_fullname):
            return True
    return False

def issubclass(cls, bases):
    """a version of issubclass that supports NetProxies"""
    if not orig_isinstance(bases, tuple):
        bases = (bases,)

    # is cls a proxy?
    if orig_isinstance(cls, NetProxy):
        return _remote_issubclass(cls, bases)

    # is one of the bases a proxy?
    for base in bases:
         if orig_isinstance(base, NetProxy):
            return _remote_issubclass(cls, bases)
    
    # plain old issubclass
    return orig_issubclass(cls, bases)

def isinstance(obj, bases):
    """a version of isinstance that supports NetProxies"""
    try:
        cls = obj.__getattr__("__class__")
    except AttributeError:
        try:
            cls = obj.__class__
        except AttributeError:
            cls = orig_type(obj)
    return issubclass(cls, bases)
    
def reload(module):
    """a version of reload() that supports NetProxies"""
    if orig_isinstance(module, NetProxy):
        return _get_conn(module).modules.__builtin__.reload(module)
    else:
        return orig_reload(module)

class _Helper(object):
    """a version of help() that supports NetProxies"""
    __repr__ = orig_help.__repr__
    
    def __call__(self, obj = None):
        if orig_isinstance(obj, NetProxy):
            print "Help on NetProxy object for an instance of %r:" % (obj.__getattr__("__class__").__name__,)
            print
            print "Doc:"
            print obj.__getattr__("__doc__")
            print
            print "Members:"
            print dir(obj)
        else:
            orig_help(obj)
help = _Helper()















