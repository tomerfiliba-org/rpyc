"""
Services are the heart of RPyC: each side of the connection exposes a *service*,
which define the capabilities available to the other side.

Note that the services by both parties need not be symmetric, e.g., one side may
exposed *service A*, while the other may expose *service B*. As long as the two
can interoperate, you're good to go.
"""
from rpyc.lib.compat import execute, is_py3k
from rpyc.core.protocol import Connection


class Service(object):
    """The service base-class. Derive from this class to implement custom RPyC
    services:

    * The name of the class implementing the ``Foo`` service should match the
      pattern ``FooService`` (suffixed by the word 'Service') ::

          class FooService(Service):
              pass

          FooService.get_service_name() # 'FOO'
          FooService.get_service_aliases() # ['FOO']

    * To supply a different name or aliases, use the ``ALIASES`` class attribute ::

          class Foobar(Service):
              ALIASES = ["foo", "bar", "lalaland"]

          Foobar.get_service_name() # 'FOO'
          Foobar.get_service_aliases() # ['FOO', 'BAR', 'LALALAND']

    * Override :func:`on_connect` to perform custom initialization

    * Override :func:`on_disconnect` to perform custom finalization

    * To add exposed methods or attributes, simply define them normally,
      but prefix their name by ``exposed_``, e.g. ::

          class FooService(Service):
              def exposed_add(self, x, y):
                  return x + y

    * All other names (not prefixed by ``exposed_``) are local (not accessible
      to the other party)

    .. note::
       You can override ``_rpyc_getattr``, ``_rpyc_setattr`` and ``_rpyc_delattr``
       to change attribute lookup -- but beware of possible **security implications!**
    """
    __slots__ = ()
    ALIASES = ()
    _protocol = Connection

    def on_connect(self, conn):
        """called when the connection is established"""
        pass
    def on_disconnect(self, conn):
        """called when the connection had already terminated for cleanup
        (must not perform any IO on the connection)"""
        pass

    # Using default defined in 'protocol.Connection._access_attr' for:
    # def _rpyc_getattr(self, name):

    def _rpyc_delattr(self, name):
        raise AttributeError("access denied")
    def _rpyc_setattr(self, name, value):
        raise AttributeError("access denied")

    @classmethod
    def get_service_aliases(cls):
        """returns a list of the aliases of this service"""
        if cls.ALIASES:
            return tuple(str(n).upper() for n in cls.ALIASES)
        name = cls.__name__.upper()
        if name.endswith("SERVICE"):
            name = name[:-7]
        return (name,)
    @classmethod
    def get_service_name(cls):
        """returns the canonical name of the service (which is its first
        alias)"""
        return cls.get_service_aliases()[0]

    exposed_get_service_aliases = get_service_aliases
    exposed_get_service_name = get_service_name

    def connect(self, channel, config={}):
        """Setup a connection via the given channel."""
        conn = self._protocol(self, channel, config)
        self.on_connect(conn)
        return conn


class VoidService(Service):
    """void service - an do-nothing service"""
    __slots__ = ()


class ModuleNamespace(object):
    """used by the :class:`SlaveService` to implement the magical
    'module namespace'"""

    __slots__ = ["__getmodule", "__cache", "__weakref__"]
    def __init__(self, getmodule):
        self.__getmodule = getmodule
        self.__cache = {}
    def __contains__(self, name):
        try:
            self[name]
        except ImportError:
            return False
        else:
            return True
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
    execution arbitrary code on the server. This is provided for compatibility
    with the classic RPyC (2.6) modus operandi.

    This service is very useful in local, secure networks, but it exposes
    a **major security risk** otherwise."""
    __slots__ = ["_conn", "exposed_namespace"]

    def on_connect(self, conn):
        self.exposed_namespace = {}
        self._conn = conn
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
        super(SlaveService, self).on_connect(conn)

    def exposed_execute(self, text):
        """execute arbitrary code (using ``exec``)"""
        execute(text, self.exposed_namespace)
    def exposed_eval(self, text):
        """evaluate arbitrary code (using ``eval``)"""
        return eval(text, self.exposed_namespace)
    def exposed_getmodule(self, name):
        """imports an arbitrary module"""
        return __import__(name, None, None, "*")
    def exposed_getconn(self):
        """returns the local connection instance to the other side"""
        return self._conn

class FakeSlaveService(VoidService):
    """VoidService that can be used for connecting to peers that operate a
    :class:`MasterService`, :class:`ClassicService`, or the old
    ``SlaveService`` (pre v3.5) without exposing any functionality to them."""
    __slots__ = ()
    exposed_namespace = None
    exposed_execute   = None
    exposed_eval      = None
    exposed_getmodule = None
    exposed_getconn   = None

class MasterService(Service):

    """Peer for a new-style (>=v3.5) :class:`SlaveService`. Use this service
    if you want to connect to a ``SlaveService`` without exposing any
    functionality to them."""
    __slots__ = ()

    def on_connect(self, conn):
        super(MasterService, self).on_connect(conn)
        # shortcuts
        conn.modules = ModuleNamespace(conn.root.getmodule)
        conn.eval = conn.root.eval
        conn.execute = conn.root.execute
        conn.namespace = conn.root.namespace
        if is_py3k:
            conn.builtin = conn.modules.builtins
        else:
            conn.builtin = conn.modules.__builtin__
        conn.builtins = conn.builtin

class ClassicService(MasterService, SlaveService):
    """Full duplex master/slave service, i.e. both parties have full control
    over the other. Must be used by both parties."""
    __slots__ = ()

class ClassicClient(MasterService, FakeSlaveService):
    """MasterService that can be used for connecting to peers that operate a
    :class:`MasterService`, :class:`ClassicService`, or the old
    ``SlaveService`` (pre v3.5) without exposing any functionality to them."""
    __slots__ = ()
