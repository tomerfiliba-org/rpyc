import sys
import importlib.abc
import importlib.util
import importlib.machinery

import rpyc.utils


class RPyCLoader(importlib.abc.Loader):
    def __init__(self, conn):
        self.conn = conn

    def create_module(self, spec):
        breakpoint()
        return
        print(self, spec)
        print(self.conn.modules, spec.name)
        module = self.conn.modules[spec.name]
        print(module.Version)
        print(module)
        return self.conn.modules[spec.name]

    def exec_module(self, module):
        remote_module = self.conn.modules[module.__spec__.name]
        print("exec_module", "local", module, module.__dict__)
        print("exec_module", "remote", remote_module, remote_module.__dict__)
        print(module.__dict__)
        return
        for key in remote_module.__dict__:
            print(key)
            if key not in ["__spec__", "__loader__"]:
                module.__dict__[key] == remote_module.__dict__[key]
        print(module.__dict__)
        return


class RPyCPathFinder(importlib.abc.MetaPathFinder):
    def __init__(self, conn, loader=None):
        self.conn = conn
        if loader is None:
            loader = RPyCLoader(self.conn)
        self.loader = loader

    def find_spec(self, name, path, target=None):
        return importlib.util.spec_from_loader(name, self.loader)
