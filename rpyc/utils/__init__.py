"""
Utilities (not part of the core protocol)
"""
import functools
import inspect
from rpyc.core import DEFAULT_CONFIG


try:
    # python3 depricated basestring, so if this causes exception catch and alias to str
    basestring
except Exception:
    basestring = str


def service(cls):
    """find and rename exposed decorated attributes"""
    for attr_name, attr_obj in inspect.getmembers(cls):  # rebind exposed decorated attributes
        exposed_prefix = getattr(attr_obj, '__exposed__', False)
        if exposed_prefix and not inspect.iscode(attr_obj):  # exclude the implementation
            renamed = exposed_prefix + attr_name
            if inspect.isclass(attr_obj):  # recurse exposed objects such as a class
                attr_obj = service(attr_obj)
            setattr(cls, attr_name, attr_obj)
            setattr(cls, renamed, attr_obj)
    return cls


def exposed(arg):
    """decorator that adds the exposed prefix information to functions which `service` uses to rebind attrs"""
    exposed_prefix = DEFAULT_CONFIG['exposed_prefix']
    if isinstance(arg, basestring):
        # When the arg is a string (i.e. `@rpyc.exposed("customPrefix_")`) the prefix
        # is partially evaluated into the wrapper. The function returned is "frozen" and used as a decorator.
        return functools.partial(_wrapper, arg)
    elif hasattr(arg, '__call__'):
        # When the arg is callable (i.e. `@rpyc.exposed`) then use default prefix and invoke
        return _wrapper(exposed_prefix, arg)
    else:
        raise TypeError('rpyc.exposed expects a callable object or a string')


def _wrapper(exposed_prefix, exposed_obj):
    exposed_obj.__exposed__ = exposed_prefix
    return exposed_obj
