from NetProxy import NetProxyWrapper, _get_conn, _get_oid


class ModuleNetProxy(NetProxyWrapper):
    """a netproxy specialzied for exposing remote modules (first tries to getattr,
    if it fails tries to import)"""
    __slots__ = ["____base__", "____cache__"]
    
    def __init__(self, proxy, base):
        NetProxyWrapper.__init__(self, proxy)
        object.__setattr__(self, "____base__", base)
        object.__setattr__(self, "____cache__", {})

    def __request__(self, handler, *args):
        return _get_conn(self).sync_request(handler, _get_oid(self), *args)

    def __getattr__(self, name):
        cache = object.__getattribute__(self, "____cache__")
        try:
            return cache[name]
        except KeyError:
            pass

        try:
            return self.__request__("handle_getattr", name)
        except AttributeError:
            pass
        
        try:
            fullname = object.__getattribute__(self, "____base__") + "." + name
            module = ModuleNetProxy(_get_conn(self).rimport(fullname), fullname)
            cache[name] = module
            return module
        except ImportError:
            raise AttributeError("'module' object has not attribute or submodule %r" % (name,))


class RootImporter(object):
    """the root of the interpreter's import hierarchy"""
    __slots__ = ["____conn__"]
    
    def __init__(self, conn):
        object.__setattr__(self, "____conn__", conn)
    
    def __getitem__(self, name):
        return _get_conn(self).rimport(name)
    
    def __getattr__(self, name):
        return ModuleNetProxy(self[name], name)
    
    def __setattr__(self, name, value):
        raise TypeError("read only type")



