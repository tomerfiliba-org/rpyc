class Service(object):
    """The service base-class. Subclass this class to implement custom RPyC
    services:
    * The name of the class implementing the 'Foo' service should match the 
      pattern 'FooService' (suffixed by the word 'Service'):
          class FooService(Service):
              pass
          FooService.get_service_name() # 'FOO'
          FooService.get_service_aliases() # ['FOO']
    * To supply a different name or aliases, use the ALIASES class attribute:
          class Foobar(Service):
              ALIASES = ["foo", "bar", "lalaland"]
          Foobar.get_service_name() # 'FOO'
          Foobar.get_service_aliases() # ['FOO', 'BAR', 'LALALAND']
    * Override on_connect to perform custom initialization
    * Override on_disconnect to perform custom finilization
    * To add exposed methods or attributes, simply define them as normally,
      but make sure their name is prefixed by 'exposed_', e.g.:
          class FooService(Service):
              def exposed_foo(self, x, y):
                  return x + y
    * All other names (not prefixed by 'exposed_') are local (not accessible 
      by the other party)
    """
    __slots__ = ["_conn"]
    ALIASES = ()
    
    def __init__(self, conn):
        self._conn = conn
    def on_connect(self):
        """called when the connection is established"""
        pass
    def on_disconnect(self):
        """called when the connection had already terminated for cleanup
        (must not perform any IO on the connection)"""
        pass
    
    def _rpyc_getattr(self, name):
        if name.startswith("exposed_"):
            name = name
        else:
            name = "exposed_" + name
        return getattr(self, name)
    def _rpyc_delattr(self, name):
        raise AttributeError("access denied")
    def _rpyc_setattr(self, name, value):
        raise AttributeError("access denied")
    
    @classmethod
    def get_service_aliases(cls):
        if cls.ALIASES:
            return tuple(str(n).upper() for n in cls.ALIASES)
        name = cls.__name__.upper()
        if name.endswith("SERVICE"):
            name = name[:-7]
        return (name,)
    @classmethod
    def get_service_name(cls):
        return cls.get_service_aliases()[0]
    
    exposed_get_service_aliases = get_service_aliases
    exposed_get_service_name = get_service_name


class VoidService(Service):
    """void service - an empty service"""
    __slots__ = ()


class ModuleNamespace(object):
    """used by the SlaveService to implement the magic 'module namespace'"""
    __slots__ = ["__getmodule", "__cache", "__weakref__"]
    def __init__(self, getmodule):
        self.__getmodule = getmodule
        self.__cache = {}
    def __getitem__(self, name):
        if type(name) is tuple:
            name = ".".join(name)
        if name not in self.__cache:
            self.__cache[name] = self.__getmodule(name)
        return self.__cache[name]
    def __getattr__(self, name):
        return self[name]

class SlaveService(Service):
    """The SlaveService allows the other side to perform arbitrary imports and
    code execution on the server. This is provided for compatibility with
    the classic RPyC (2.6) modus operandi. 
    This service is very useful in local, secured networks, but it exposes
    a major security risk otherwise."""
    __slots__ = ["exposed_namespace"]
    
    def on_connect(self):
        self.exposed_namespace = {}
        self._conn._config.update(dict(
            allow_all_attrs = True,
            allow_pickle = True, 
            allow_getattr = True,
            allow_setattr = True,
            allow_delattr = True,
            import_custom_exceptions = True,
            instantiate_custom_exceptions = True,
            instantiate_oldstyle_exceptions = True,
        ))
        # shortcuts
        self._conn.modules = ModuleNamespace(self._conn.root.getmodule)
        self._conn.eval = self._conn.root.eval
        self._conn.execute = self._conn.root.execute
        self._conn.namespace = self._conn.root.namespace
        self._conn.builtin = self._conn.modules.__builtin__
    
    def exposed_execute(self, text):
        exec text in self.exposed_namespace
    def exposed_eval(self, text):
        return eval(text, self.exposed_namespace)
    def exposed_getmodule(self, name):
        return __import__(name, None, None, "*")
    def exposed_getconn(self):
        return self._conn







