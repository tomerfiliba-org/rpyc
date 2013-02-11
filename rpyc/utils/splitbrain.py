import sys
import threading
from contextlib import contextmanager
try:
    import __builtin__ as builtins
except ImportError:
    import builtins # python 3+
from types import ModuleType

router = threading.local()

routed_modules = ["os", "os.path", "platform", "ntpath", "posixpath", "zipimport", "genericpath", 
    "posix", "nt", "signal", "time", "sysconfig", "_locale", "locale", "socket", "_socket", "ssl", "_ssl",
    "struct", "_struct", "_symtable", "errno", "fcntl", "grp", "imp", "pwd", "select", "spwd", 
    "syslog", "thread", "_io", "io", "subprocess", "_subprocess", "datetime", "mmap", "msvcrt"]

class RoutedModule(ModuleType):
    def __init__(self, realmod):
        ModuleType.__init__(self, realmod.__name__, getattr(realmod, "__doc__", None))
        object.__setattr__(self, "__realmod__", realmod)
        object.__setattr__(self, "__file__", getattr(realmod, "__file__", None))
    def __repr__(self):
        modname = object.__getattribute__(self, "__name__")
        try:
            self.__currmod__
        except AttributeError:
            return "<module %r (stale)>" % (modname,)
        else:
            if self.__file__:
                return "<module %r from %r>" % (modname, self.__file__)
            else:
                return "<module %r (built-in)>" % (modname,)
    def __getattribute__(self, name):
        if name == "__realmod__":
            return object.__getattribute__(self, "__realmod__")
        elif name == "__name__":
            return object.__getattribute__(self, "__name__")
        elif name == "__currmod__":
            modname = object.__getattribute__(self, "__name__")
            if hasattr(router, "conn"):
                return router.conn.modules[modname]
                #mod = router.conn.modules._ModuleNamespace__cache.getattr(modname, None)
                #if mod is None:
                #    raise AttributeError("No module named %s" % (modname,))
                #else:
                #    return mod
            elif modname in sys.modules:
                return object.__getattribute__(self, "__realmod__")
            else:
                raise AttributeError("No module named %s" % (modname,))
        else:
            return getattr(self.__currmod__, name)
    def __setattr__(self, name, val):
        return setattr(self.__currmod__, name, val)

_orig_import = builtins.__import__

def _importer(modname, *args, **kwargs):
    if hasattr(router, "conn"):
        mod = router.conn.modules[modname]
        rmod = RoutedModule(mod)
        sys.modules[modname] = rmod
        return rmod
    else:
        return _orig_import(modname, *args, **kwargs)

_enabled = False

def enable():
    """Enables (activates) the Splitbrain machinery"""
    global _enabled
    for modname in routed_modules:
        try:
            realmod = __import__(modname, [], [], "*")
        except ImportError:
            pass
        else:
            sys.modules[modname] = RoutedModule(realmod)
    builtins.__import__ = _importer
    _enabled = True

def disable():
    """Disables (restores) the Splitbrain machinery"""
    global _enabled
    _enabled = False
    for modname, mod in sys.modules.items():
        if isinstance(mod, RoutedModule):
            sys.modules[modname] = mod.__realmod__
    builtins.__import__ = _orig_import

@contextmanager
def splitbrain(conn):
    """Enter a splitbrain context in which imports take place over the given RPyC connection (expected to 
    be a SlaveService). You can enter this context only after calling ``enable()``"""
    if not _enabled:
        raise ValueError("Splitbrain not enabled")
    prev_conn = getattr(router, "conn", None)
    prev_modules = sys.modules.copy()
    router.conn = conn
    try:
        yield
    finally:
        sys.modules.clear()
        sys.modules.update(prev_modules)
        router.conn = prev_conn
        if not router.conn:
            del router.conn

@contextmanager
def localbrain():
    """Return to operate on the local machine. You can enter this context only after calling ``enable()``"""
    if not _enabled:
        raise ValueError("Splitbrain not enabled")
    prev_conn = getattr(router, "conn", None)
    prev_modules = sys.modules.copy()
    if hasattr(router, "conn"):
        del router.conn
    try:
        yield
    finally:
        sys.modules.clear()
        sys.modules.update(prev_modules)
        router.conn = prev_conn
        if not router.conn:
            del router.conn


if __name__ == "__main__":
    import rpyc
    c = rpyc.classic.connect("192.168.1.143")
    enable()
    
#    import os
#    print 1, os.getcwd()
#    from os.path import abspath
#    print 2, abspath(".")
#    
#    with splitbrain(c):
#        print 3, abspath(".")
#        from os.path import abspath
#        print 4, abspath(".")
#        print 5, os.getcwd()
#        import twisted
#        print 6, twisted
#        
#        with localbrain():
#            print 6.1, os.getcwd()
#
#    print 7, twisted
#    try:
#        print twisted.version
#    except AttributeError:
#        print 8, "can't access twisted.version"
#    else:
#        assert False
#
#    try:
#        import twisted
#    except ImportError:
#        print 9, "can't import twisted"
#    else:
#        assert False
#
#    with splitbrain(c):
#        print 10, twisted
#        print 11, twisted.version
#    print "======================================================================"
    
    import socket
    import telnetlib
    s = socket.socket()
    s.bind(("0.0.0.0", 23))
    s.listen(1)
    host, port = s.getsockname()
    
    with splitbrain(c):
        t = telnetlib.Telnet(host, port, timeout = 5)
        print t.sock.getsockname()





