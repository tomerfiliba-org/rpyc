import sys
import functools
try:
    import __builtin__ as builtins
except ImportError:
    import builtins # python 3+
import threading
from types import ModuleType


PATCHED_MODULES = ["os", "subprocess", "socket", "_socket", "select", "urllib", "platform", 
    "tempfile", "posix", "nt", "io", "_io", "ssl", "_ssl", "signal", "os.path", "posixpath",
    "ntpath", "stat", "sysconfig", "tarfile", "zipfile", "commands", "glob", "shutil",
    "pexpect"]

PATCHED_ATTRIBUTES = {
    "sys" : ["byteorder", "platform", "getfilesystemencoding", "getdefaultencoding"],
            # 'stderr', 'stdin', 'stdout'
}

class BaseRoutedModule(ModuleType):
    pass

orig_import = builtins.__import__
router = threading.local()

def thread_local_import(*args, **kwargs):
    if hasattr(router, "importer"):
        return router.importer(*args, **kwargs)
    else:
        return orig_import(*args, **kwargs)

def build_routed_module(modname, realmod):
    def getmod():
        if not hasattr(router, "modules") or modname not in router.modules:
            return realmod
        return router.modules[modname]
    
    class RoutedModule(BaseRoutedModule):
        def __init__(self):
            BaseRoutedModule.__init__(self, "routed " + modname)
        def __dir__(self):
            return dir(getmod())
        def __getattribute__(self, name):
            return getattr(getmod(), name)
        def __setattr__(self, name, value):
            setattr(getmod(), name, value)
        def __delattr__(self, name):
            delattr(getmod(), name)
    
    return RoutedModule()

def build_routed_attr_module(modname, realmod, attrlist):
    def getmod(name):
        if name not in attrlist or not hasattr(router, "modules") or not modname in router.modules:
            return realmod
        return router.modules[modname]
    
    class RoutedAttrModule(BaseRoutedModule):
        def __init__(self):
            BaseRoutedModule.__init__(self, "routedattr " + modname)
        def __dir__(self):
            return dir(getmod(None))
        def __getattribute__(self, name):
            return getattr(getmod(name), name)
        def __setattr__(self, name, value):
            setattr(getmod(name), name, value)
        def __delattr__(self, name):
            delattr(getmod(name), name)
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
        else:
            sys.modules[modname] = build_routed_attr_module(modname, mod, frozenset(attrlist))

    builtins.__import__ = thread_local_import
    
    for funcname in ["open", "execfile", "file"]:
        if not hasattr(builtins, funcname):
            continue
        def mkfunc(funcname, origfunc):
            @functools.wraps(getattr(builtins, funcname))
            def tlbuiltin(*args, **kwargs):
                if hasattr(router, "builtins"):
                    func = getattr(router.builtins, funcname)
                else:
                    func = origfunc
                return func(*args, **kwargs)
            return tlbuiltin
        setattr(builtins, funcname, mkfunc(funcname, getattr(builtins, funcname)))


class NullModule(object):
    __slots__ = ["__name__"]
    def __init__(self, modname):
        object.__setattr__(self, "__name__", modname)
    def __getattribute__(self, name):
        modname = object.__getattribute__(self, "__name__")
        raise AttributeError("Nonexistent module %s (%r)" % (modname, name))
    def __setattr__(self, name, value):
        modname = object.__getattribute__(self, "__name__")
        raise AttributeError("Nonexistent module %s (%r)" % (modname, name))
    def __delattr__(self, name):
        modname = object.__getattribute__(self, "__name__")
        raise AttributeError("Nonexistent module %s (%r)" % (modname, name))


class Splitbrain(object):
    def __init__(self, conn):
        self.conn = conn
        self._stack = []
        self._stack_index = 0
    
    def close(self):
        while self._stack:
            self.restore()
        self.conn.close()
    
    def _rpyc_import(self, name, *args):
        self._stack_index -= 1
        try:
            try:
                prev_importer = self._stack[self._stack_index][2]
            except IndexError:
                def prev_importer(name, *args):
                    raise ImportError("No module named %s" % (name,))
                
            try:
                return prev_importer(name, *args)
            except ImportError:
                mod = self.conn.modules[name]
                sys.modules[name] = build_routed_module(name, NullModule(name))
                return sys.modules[name]
        finally:
            self._stack_index += 1
    
    def activate(self):
        self._stack.append((getattr(router, "modules", None), 
            getattr(router, "builtins", None), getattr(router, "importer", orig_import),
            self.conn.modules.sys.stdin, self.conn.modules.sys.stdout, 
            self.conn.modules.sys.stderr))
        router.importer = self._rpyc_import
        router.modules = self.conn.modules
        router.builtins = self.conn.builtin
        self.conn.modules.sys.stdin = sys.stdin
        self.conn.modules.sys.stdout = sys.stdout
        self.conn.modules.sys.stderr = sys.stderr
    
    def restore(self):
        router.modules, router.builtins, router.importer, si, so, se = self._stack.pop(-1)
        self.conn.modules.sys.stdin = si
        self.conn.modules.sys.stdout = so
        self.conn.modules.sys.stderr = se
        if router.modules is None:
            del router.modules
        if router.builtins is None:
            del router.builtins
        if router.importer is None:
            del router.importer
    
    def __enter__(self):
        self.activate()
    def __exit__(self, t, v, tb):
        if self._stack:
            self.restore()


#if __name__ == "__main__":
#    import rpyc
#    patch()
#
#    import sys
#    import platform
#    print platform.platform()
#    print sys.platform
#
#    with open("test.txt", "w") as f:
#        f.write("hello")
#        
#    myhost = Splitbrain(rpyc.classic.connect("linuxbox"))
#    with myhost:
#        print platform.platform()
#        print sys.platform
#        import termios
#        print termios.tcsendbreak
#        
#        import subprocess
#        p = subprocess.Popen(["ls"], stdout = -1)
#        print repr(p.stdout.read())
#        p.wait()
#
#        with open("/etc/bash.bashrc", "r") as f:
#            print f.readline()
#    
#    print platform.platform()
#    print sys.platform
#    
#    subprocess.Popen
#
#    try:
#        termios.tcsendbreak
#    except AttributeError as ex:
#        print ex
#    else:
#        raise AssertionError("termios.tcsendbreak shouldn't be accessible here")
#
#    with open("test.txt", "r") as f:
#        assert f.read() == "hello"
#        
#    myhost.close()



