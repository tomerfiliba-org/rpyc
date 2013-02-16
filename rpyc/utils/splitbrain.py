import sys
import threading
from contextlib import contextmanager
import functools
import gc
try:
    import __builtin__ as builtins
except ImportError:
    import builtins # python 3+
from types import ModuleType

router = threading.local()

routed_modules = set(["os", "os.path", "platform", "ntpath", "posixpath", "zipimport", "genericpath", 
    "posix", "nt", "signal", "time", "sysconfig", "_locale", "locale", "socket", "_socket", "ssl", "_ssl",
    "struct", "_struct", "_symtable", "errno", "fcntl", "grp", "imp", "pwd", "select", "spwd", 
    "syslog", "thread", "_io", "io", "subprocess", "_subprocess", "datetime", "mmap", "msvcrt"])

class RoutedModule(ModuleType):
    def __init__(self, realmod):
        ModuleType.__init__(self, realmod.__name__, getattr(realmod, "__doc__", None))
        object.__setattr__(self, "__realmod__", realmod)
        object.__setattr__(self, "__file__", getattr(realmod, "__file__", None))
    def __repr__(self):
        if self.__file__:
            return "<module %r from %r>" % (self.__name__, self.__file__)
        else:
            return "<module %r (built-in)>" % (self.__name__,)
    def __dir__(self):
        return dir(self.__currmod__)
    def __getattribute__(self, name):
        if name == "__realmod__":
            return object.__getattribute__(self, "__realmod__")
        elif name == "__name__":
            return object.__getattribute__(self, "__name__")
        elif name == "__currmod__":
            modname = object.__getattribute__(self, "__name__")
            if hasattr(router, "conn"):
                return router.conn.modules[modname]
            else:
                return object.__getattribute__(self, "__realmod__")
        else:
            return getattr(self.__currmod__, name)
    def __delattr__(self, name, val):
        return setattr(self.__currmod__, name, val)
    def __setattr__(self, name, val):
        return setattr(self.__currmod__, name, val)

routed_sys_attrs = set(["byteorder", "platform", "getfilesystemencoding", "getdefaultencoding"])

class RoutedSysModule(ModuleType):
    def __init__(self):
        ModuleType.__init__(self, "sys", sys.__doc__)
    def __dir__(self):
        return dir(sys)
    def __getattribute__(self, name):
        if name in routed_sys_attrs and hasattr(router, "conn"):
            return getattr(router.conn.modules["sys"], name)
        else:
            return getattr(sys, name)
    def __setattr__(self, name, value):
        if name in routed_sys_attrs and hasattr(router, "conn"):
            setattr(router.conn.modules["sys"], name, value)
        else:
            setattr(sys, name, value)

sys2 = RoutedSysModule()

class RemoteModule(ModuleType):
    def __init__(self, realmod):
        ModuleType.__init__(self, realmod.__name__, getattr(realmod, "__doc__", None))
        object.__setattr__(self, "__file__", getattr(realmod, "__file__", None))
    def __repr__(self):
        try:
            self.__currmod__
        except (AttributeError, ImportError):
            return "<module %r (stale)>" % (self.__name__,)
        if self.__file__:
            return "<module %r from %r>" % (self.__name__, self.__file__)
        else:
            return "<module %r (built-in)>" % (self.__name__,)
    def __dir__(self):
        return dir(self.__currmod__)

    def __getattribute__(self, name):
        if name == "__name__":
            return object.__getattribute__(self, "__name__")
        elif name == "__currmod__":
            modname = object.__getattribute__(self, "__name__")
            if not hasattr(router, "conn"):
                raise AttributeError("Module %r is not available in this context" % (modname,))
            mod = router.conn.modules._ModuleNamespace__cache.get(modname)
            if not mod:
                raise AttributeError("Module %r is not available in this context" % (modname,))
            return mod
        else:
            return getattr(self.__currmod__, name)
    def __delattr__(self, name, val):
        return setattr(self.__currmod__, name, val)
    def __setattr__(self, name, val):
        return setattr(self.__currmod__, name, val)


_orig_import = builtins.__import__

def _importer(modname, *args, **kwargs):
    if not hasattr(router, "conn"):
        return _orig_import(modname, *args, **kwargs)
    existing = sys.modules.get(modname, None)
    if type(existing) is RoutedModule:
        return existing
    
    mod = router.conn.modules[modname]
    if existing and type(existing) is RemoteModule:
        return existing
    rmod = RemoteModule(mod)
    sys.modules[modname] = rmod
    return rmod

_enabled = False
_prev_builtins = {}

def enable():
    """Enables (activates) the Splitbrain machinery"""
    global _enabled
    if _enabled:
        return
    sys.modules["sys"] = sys2
    for modname in routed_modules:
        try:
            realmod = __import__(modname, [], [], "*")
        except ImportError:
            pass
        else:
            rmod = RoutedModule(realmod)
            sys.modules[modname] = rmod
            for ref in gc.get_referrers(realmod):
                if not isinstance(ref, dict) or "__name__" not in ref or ref.get("__file__") is None:
                    continue
                if ref["__name__"] in routed_modules or ref["__name__"].startswith("rpyc"):
                    continue
                for k, v in ref.items():
                    if v is realmod:
                        ref[k] = rmod

    builtins.__import__ = _importer
    for funcname in ["open", "execfile", "file"]:
        if not hasattr(builtins, funcname):
            continue
        def mkfunc(funcname, origfunc):
            @functools.wraps(getattr(builtins, funcname))
            def tlbuiltin(*args, **kwargs):
                if hasattr(router, "conn"):
                    func = getattr(router.conn.builtins, funcname)
                else:
                    func = origfunc
                return func(*args, **kwargs)
            return tlbuiltin
        origfunc = getattr(builtins, funcname)
        _prev_builtins[funcname] = origfunc
        setattr(builtins, funcname, mkfunc(funcname, origfunc))
    
    _enabled = True

def disable():
    """Disables (restores) the Splitbrain machinery"""
    global _enabled
    if not _enabled:
        return
    _enabled = False
    for funcname, origfunc in _prev_builtins.items():
        setattr(builtins, funcname, origfunc)
    for modname, mod in sys.modules.items():
        if isinstance(mod, RoutedModule):
            sys.modules[modname] = mod.__realmod__
            for ref in gc.get_referrers(mod):
                if isinstance(ref, dict) and "__name__" in ref and ref.get("__file__") is not None:
                    for k, v in ref.items():
                        if v is mod:
                            ref[k] = mod.__realmod__
    sys.modules["sys"] = sys
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
    prev_stdin = conn.modules.sys.stdin
    prev_stdout = conn.modules.sys.stdout
    prev_stderr = conn.modules.sys.stderr
    conn.modules["sys"].stdin = sys.stdin
    conn.modules["sys"].stdout = sys.stdout
    conn.modules["sys"].stderr = sys.stderr
    try:
        yield
    finally:
        conn.modules["sys"].stdin = prev_stdin
        conn.modules["sys"].stdout = prev_stdout
        conn.modules["sys"].stderr = prev_stderr
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

splitbrain.enable = enable
splitbrain.disable = disable



