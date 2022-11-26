"""
Services are the heart of RPyC: each side of the connection exposes a *service*,
which define the capabilities available to the other side.

Note that the services by both parties need not be symmetric, e.g., one side may
exposed *service A*, while the other may expose *service B*. As long as the two
can interoperate, you're good to go.
"""
import importlib.util
from functools import partial

from rpyc.lib import hybridmethod
from rpyc.lib.compat import execute
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

    @hybridmethod
    def _connect(self, channel, config={}):
        """Setup a connection via the given channel."""
        if isinstance(self, type):  # autovivify if accessed as class method
            self = self()
        # Note that we are here passing in `self` as root object for backward
        # compatibility and convenience. You could pass in a different root if
        # you wanted:
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
        self.__cache = {m: self.__getmodule(m) for m in ('builtins', 'importlib.util')}

    def __contains__(self, name):
        """Returns True if a module CAN be imported (the loader may still fail to execute module)"""
        return self.__cache['importlib.util']._find_spec_from_path(name) is not None

    def __getitem__(self, name):
        """Acts as a 'read-through-cache' for results of getmodule"""
        if name not in self.__cache:
            self.__cache[name] = self.__getmodule(name)
        return self.__cache[name]

    def __getattr__(self, name):
        """Provides dot notation access to modules"""
        try:
            return self[name]
        except ImportError:
            raise AttributeError(name)


class Slave(object):
    __slots__ = ["_conn", "namespace"]

    def __init__(self):
        self._conn = None
        self.namespace = {}

    def execute(self, text):
        """execute arbitrary code (using ``exec``)"""
        execute(text, self.namespace)

    def eval(self, text):
        """evaluate arbitrary code (using ``eval``)"""
        return eval(text, self.namespace)

    def getmodule(self, name):
        """imports an arbitrary module"""
        if type(name) is tuple:
            name = ".".join(name)
        return importlib.import_module(name)

    def getconn(self):
        """returns the local connection instance to the other side"""
        return self._conn


class SlaveService(Slave, Service):
    """The SlaveService allows the other side to perform arbitrary imports and
    execution arbitrary code on the server. This is provided for compatibility
    with the classic RPyC (2.6) modus operandi.

    This service is very useful in local, secure networks, but it exposes
    a **major security risk** otherwise."""
    __slots__ = ()

    def on_connect(self, conn):
        self._conn = conn
        self._conn._config.update(dict(
            allow_all_attrs=True,
            allow_pickle=True,
            allow_getattr=True,
            allow_setattr=True,
            allow_delattr=True,
            allow_exposed_attrs=False,
            import_custom_exceptions=True,
            instantiate_custom_exceptions=True,
            instantiate_oldstyle_exceptions=True,
        ))
        super().on_connect(conn)


class FakeSlaveService(VoidService):
    """VoidService that can be used for connecting to peers that operate a
    :class:`MasterService`, :class:`ClassicService`, or the old
    ``SlaveService`` (pre v3.5) without exposing any functionality to them."""
    __slots__ = ()
    exposed_namespace = None
    exposed_execute = None
    exposed_eval = None
    exposed_getmodule = None
    exposed_getconn = None


class MasterService(Service):

    """Peer for a new-style (>=v3.5) :class:`SlaveService`. Use this service
    if you want to connect to a ``SlaveService`` without exposing any
    functionality to them."""
    __slots__ = ()

    def on_connect(self, conn):
        super().on_connect(conn)
        self._install(conn, conn.root)

    @staticmethod
    def _install(conn, slave):
        modules = ModuleNamespace(slave.getmodule)
        conn.modules = modules
        conn.eval = slave.eval
        conn.execute = slave.execute
        conn.namespace = slave.namespace
        conn.builtins = modules.builtins
        conn.builtin = modules.builtins  # TODO: cruft from py2 that requires cleanup elsewhere and CHANGELOG note
        from rpyc.utils.classic import teleport_function
        conn.teleport = partial(teleport_function, conn)


class ClassicService(MasterService, SlaveService):
    """Full duplex master/slave service, i.e. both parties have full control
    over the other. Must be used by both parties."""
    __slots__ = ()


class ClassicClient(MasterService, FakeSlaveService):
    """MasterService that can be used for connecting to peers that operate a
    :class:`MasterService`, :class:`ClassicService` without exposing any
    functionality to them."""
    __slots__ = ()
