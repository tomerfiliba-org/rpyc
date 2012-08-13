import sys
import rpyc
import __builtin__
import threading
from types import ModuleType


router = threading.local()
router.modules = {}

def build_routed_module(modname, realmod):
    def getmod():
        if not hasattr(router, "modules") or not modname in router.modules:
            return realmod
        return router[modname]
    
    class RoutedModule(ModuleType):
        def __init__(self):
            ModuleType.__init__(self, "routed " + modname)
            #object.__setattr__(self, "__file__", __file__)
        def __getattribute__(self, name):
            return getattr(getmod(), name)
        def __setattr__(self, name, value):
            setattr(getmod(), name, value)
        def __delattr__(self, name):
            delattr(getmod(), name)
    
    return RoutedModule()


class Splitbrain(object):
    #PATCHED_BUILTINS = ["open", "execfile", "file"]
    #PATCHED_SYS = ["byteorder", "platform", 'stderr', 'stdin', 'stdout', 'getfilesystemencoding',
    #    'getdefaultencoding']
    PATCHED_MODULES = ["os", "subprocess", "socket", "urllib", "platform", "tempfile", "posix", "nt"]
    
    def __init__(self, conn, patched_modules = PATCHED_MODULES):
        self.conn = conn
        self.patched_modules = set(patched_modules)
        self._stack = [{}, __builtin__.__import__]
        self._patch()

    def _patch(self):
        for key, mod in sys.modules.items():
            if not isinstance(mod, ModuleType) or mod.__name__ not in self.patched_modules:
                continue
            sys.modules[key] = build_routed_module(key, mod)

        for key, mod in sys.modules.items():
            if not isinstance(mod, ModuleType) or isinstance(mod, rpyc.BaseNetref):
                continue
            for name, attr in mod.__dict__.items():
                if isinstance(attr, ModuleType) and attr.__name__ in self.patched_modules:
                    setattr(mod, name, sys.modules[key])
    
    def _rpyc_import(self, name, *args):
        _, orig_import = self._stack[-1]
        print "in _rpyc_import", name
        if name in self.patched_modules:
            print "!! subverting"
            mod = self.conn.modules[name]
        else:
            try:
                mod = orig_import(name, *args)
            except ImportError:
                print "!! cannot import locally", name
                mod = self.conn.modules[name]
        return mod
    
    def __enter__(self):
        self._stack.append((router.modules, __builtin__.__import__))
        router.modules = self.conn.modules
        __builtin__.__import__ = self._rpyc_import
    
    def __exit__(self, t, v, tb):
        router.modules, __builtin__.__import__ = self._stack.pop(-1)



if __name__ == "__main__":
    import rpyc
    conn = rpyc.classic.connect("tp-tomerf.il.xiv.ibm.com")
    s = Splitbrain(conn)
    
    with s:
        import platform
        print platform.platform()
        import win32file
        print win32file
    
    import platform
    print platform.platform()




