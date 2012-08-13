import sys
import __builtin__
import threading
from types import ModuleType


router = threading.local()
router.modules = {}

PATCHED_MODULES = ["os", "subprocess", "socket", "_socket", "select", "urllib", "platform", 
    "tempfile", "posix", "nt", "io", "_io", "ssl", "_ssl", "signal", "os.path", "posixpath",
    "ntpath", "stat", "sysconfig"]
PATCHED_ATTRIBUTES = {
    "sys" : ["byteorder", "platform", 'stderr', 'stdin', 'stdout', 'getfilesystemencoding',
            'getdefaultencoding'],
    "__builtin__" : ["open", "execfile", "file"]
}

class BaseRoutedModule(ModuleType):
    pass

def build_routed_module(modname, realmod):
    def getmod():
        if not hasattr(router, "modules") or modname not in router.modules:
            return realmod
        return router.modules[modname]
    
    class RoutedModule(BaseRoutedModule):
        def __init__(self):
            BaseRoutedModule.__init__(self, "routed " + modname)
        def __getattribute__(self, name):
            return getattr(getmod(), name)
        def __setattr__(self, name, value):
            setattr(getmod(), name, value)
        def __delattr__(self, name):
            delattr(getmod(), name)
    
    return RoutedModule()

def build_routed_attr_module(modname, realmod, attrlist):
    def getmod():
        if not modname in attrlist or not hasattr(router, "modules") or not modname in router.modules :
            return realmod
        return router.modules[modname]
    
    class RoutedAttrModule(BaseRoutedModule):
        def __init__(self):
            BaseRoutedModule.__init__(self, "routedattr " + modname)
        def __getattribute__(self, name):
            return getattr(getmod(), name)
        def __setattr__(self, name, value):
            setattr(getmod(), name, value)
        def __delattr__(self, name):
            delattr(getmod(), name)
    return RoutedAttrModule()


def patch(patched_modules = PATCHED_MODULES, patched_attributes = PATCHED_ATTRIBUTES):
    for modname in patched_modules:
        try:
            mod = __import__(modname)
        except ImportError:
            pass
        else:
            if not isinstance(sys.modules[modname], BaseRoutedModule):
                sys.modules[modname] = build_routed_module(modname, mod)

    for mod in sys.modules.values():
        if not isinstance(mod, ModuleType) or isinstance(mod, BaseRoutedModule):
            continue
        for name, attr in mod.__dict__.items():
            if isinstance(attr, ModuleType) and isinstance(sys.modules.get(attr.__name__), BaseRoutedModule):
                setattr(mod, name, sys.modules[attr.__name__])
    
    for modname, attrlist in patched_attributes.items():
        try:
            mod = __import__(modname)
        except ImportError:
            pass
        sys.modules[modname] = build_routed_attr_module(modname, mod, frozenset(attrlist))


class Splitbrain(object):
    def __init__(self, conn):
        self.conn = conn
        self._stack = [{}, __builtin__.__import__]
    
    def _rpyc_import(self, name, *args):
        _, orig_import = self._stack[-1]
        try:
            return orig_import(name, *args)
        except ImportError:
            mod = self.conn.modules[name]
            sys.modules[name] = build_routed_module(name, None)
            return sys.modules[name]
    
    def activate(self):
        self._stack.append((router.modules, __builtin__.__import__))
        router.modules = self.conn.modules
        __builtin__.__import__ = self._rpyc_import
    
    def restore(self):
        router.modules, __builtin__.__import__ = self._stack.pop(-1)
    
    def __enter__(self):
        self.activate()
    def __exit__(self, t, v, tb):
        self.restore()



#if __name__ == "__main__":
#    import rpyc
#    patch()
#
#    myhost = Splitbrain(rpyc.classic.connect("tp-tomerf.il.xiv.ibm.com"))
#    
#    import platform
#    print platform.platform()
#
#    with myhost:
#        print platform.platform()
#        import win32file
#        print win32file.CreateFile
#    
#    try:
#        win32file.CreateFile
#    except Exception:
#        pass
#    else:
#        raise AssertionError("win32file shouldn't be accessible here")
#    
#    print platform.platform()
#
#    with myhost:
#        print platform.platform()
#        print win32file.CreateFile
#
#    print platform.platform()

