import pyximport; pyximport.install()
from subinterpreter import SubInterpreter
from types import ModuleType
import __builtin__ as orig_builtin


class Splitbrain(object):
    PATCHED_BUILTINS = ["open", "execfile", "file"]
    PATCHED_SYS = ["byteorder", "platform", 'stderr', 'stdin', 'stdout', 'getfilesystemencoding',
        'getdefaultencoding']
    PATCHED_MODULES = ["os", "subprocess", "socket", "urllib", "platform", "tempfile", "posix", 
        "nt"]
    SKIP_MODULES = ["site", "sysconfig"]
    
    def __init__(self, conn, patched_modules = PATCHED_MODULES, patched_builtins = PATCHED_BUILTINS, 
            patched_sys = PATCHED_SYS):
        self.conn = conn
        self.patched_modules = set(patched_modules)
        self.patched_builtins = set(patched_builtins)
        self.patched_sys = set(patched_sys)
        self.subint = SubInterpreter()
        self.first_time = True

    def _patch_module(self, mod):
        import sys
        for n, v in mod.__dict__.items():
            if isinstance(v, ModuleType) and v.__name__ in self.patched_modules:
                setattr(v, n, sys.modules[v.__name__])

    def _install_import_hook(self):
        import sys
        import __builtin__
        
        for modname in self.patched_modules:
            try:
                sys.modules[modname] = self.conn.modules[modname]
            except ImportError:
                pass
        
        for bltin in self.patched_builtins:
            if hasattr(__builtin__, bltin): 
                setattr(__builtin__, bltin, getattr(self.conn.builtin, bltin))

        for psys in self.patched_sys:
            if hasattr(sys, psys): 
                setattr(sys, psys, getattr(self.conn.modules.sys, psys))

        for mod in sys.modules.values():
            if (isinstance(mod, ModuleType) and mod.__name__ not in self.SKIP_MODULES and 
                    not mod.__name__ in self.patched_modules):
                self._patch_module(mod)
        
        #orig_import = __builtin__.__import__
        #def splitbrain_import(name, *args, **kwargs):
        #    print "SPLITBRAIN IMPORT", name
        #    if name in self.overriden_modules:
        #        mod = self.conn.modules[name]
        #    else:
        #        mod = orig_import(name, *args, **kwargs)
        #        self._patch_module(mod)
        #    return mod
        #__builtin__.__import__ = splitbrain_import

    def __enter__(self):
        self.subint.__enter__()
        if self.first_time:
            self.first_time = False
            #self._install_import_hook()
    
    def __exit__(self, t, v, tb):
        self.subint.__exit__(t, v, tb)



