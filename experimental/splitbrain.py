import pyximport; pyximport.install()
from subinterpreter import SubInterpreter
from types import ModuleType


class Splitbrain(object):
    OVERRIDEN_MODULES = ["os", "popen", "socket", "urllib", "platform"]
    
    def __init__(self, conn, overriden_modules = OVERRIDEN_MODULES):
        self.conn = conn
        self.overriden_modules = set(overriden_modules)
        self.subint = SubInterpreter()
        self.first_time = True
    
    def close(self):
        self.subint.close()
        self.connc.close()

    def _patch_module(self, mod):
        for n, v in mod.__dict__.items():
            if isinstance(v, ModuleType) and v.__name__ in self.overriden_modules:
                setattr(v, n, self.conn.modules[v.__name__])

    def _install_import_hook(self):
        import sys
        import __builtin__
        
        print "_install_import_hook1"
        for mod in sys.modules.values():
            if isinstance(mod, ModuleType):
                self._patch_module(mod)

        print "_install_import_hook2"
        
        orig_import = __builtin__.__import__
        def splitbrain_import(name, *args, **kwargs):
            if name in self.overriden_modules:
                mod = self.conn.modules[name]
            else:
                mod = orig_import(name, *args, **kwargs)
                self._patch_module(mod)
            return mod
        __builtin__.__import__ = splitbrain_import
        print "_install_import_hook3"

    def __enter__(self):
        self.subint.__enter__()
        if self.first_time:
            self.first_time = False
            self._install_import_hook()
    
    def __exit__(self, t, v, tb):
        self.subint.__exit__(t, v, tb)



