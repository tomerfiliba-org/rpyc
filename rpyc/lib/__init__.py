"""
A library of various helpers functions and classes
"""
import inspect
import sys
import socket
import logging
import threading
import time
import random
from rpyc.lib.compat import maxint  # noqa: F401


SPAWN_THREAD_PREFIX = 'RpycSpawnThread'


class MissingModule(object):
    __slots__ = ["__name"]

    def __init__(self, name):
        self.__name = name

    def __getattr__(self, name):
        if name.startswith("__"):  # issue 71
            raise AttributeError(f"module {self.__name!r} not found")
        raise ImportError(f"module {self.__name!r} not found")

    def __bool__(self):
        return False
    __nonzero__ = __bool__


def safe_import(name):
    try:
        mod = __import__(name, None, None, "*")
    except ImportError:
        mod = MissingModule(name)
    except Exception:
        # issue 72: IronPython on Mono
        if sys.platform == "cli" and name == "signal":  # os.name == "posix":
            mod = MissingModule(name)
        else:
            raise
    return mod


def setup_logger(quiet=False, logfile=None, namespace=None):
    opts = {}
    if quiet:
        opts['level'] = logging.ERROR
        opts['format'] = '%(asctime)s %(levelname)s: %(message)s'
        opts['datefmt'] = '%b %d %H:%M:%S'
    else:
        opts['level'] = logging.DEBUG
        opts['format'] = '%(asctime)s %(levelname)s %(name)s[%(threadName)s]: %(message)s'
        opts['datefmt'] = '%b %d %H:%M:%S'
    if logfile:
        opts['filename'] = logfile
    logging.basicConfig(**opts)
    return logging.getLogger('rpyc' if namespace is None else f'rpyc.{namespace}')


class hybridmethod(object):
    """Decorator for hybrid instance/class methods that will act like a normal
    method if accessed via an instance, but act like classmethod if accessed
    via the class."""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        return self.func.__get__(cls if obj is None else obj, obj)

    def __set__(self, obj, val):
        raise AttributeError("Cannot overwrite method")


def hasattr_static(obj, attr):
    """Returns if `inspect.getattr_static` can find an attribute of ``obj``."""
    try:
        inspect.getattr_static(obj, attr)
    except AttributeError:
        return False
    else:
        return True


def spawn(*args, **kwargs):
    """Start and return daemon thread. ``spawn(func, *args, **kwargs)``."""
    func, args = args[0], args[1:]
    str_id_pack = '-'.join([f'{i}' for i in get_id_pack(func)])
    thread = threading.Thread(name=f'{SPAWN_THREAD_PREFIX}-{str_id_pack}', target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread


def spawn_waitready(init, main):
    """
    Start a thread that runs ``init`` and then ``main``. Wait for ``init`` to
    be finished before returning.

    Returns a tuple ``(thread, init_result)``.
    """
    event = threading.Event()
    stack = [event]     # used to exchange arguments with thread, so `event`
    # can be deleted when it has fulfilled its purpose.

    def start():
        stack.append(init())
        stack.pop(0).set()
        return main()
    thread = spawn(start)
    event.wait()
    return thread, stack.pop()


class Timeout(object):

    def __init__(self, timeout):
        if isinstance(timeout, Timeout):
            self.finite = timeout.finite
            self.tmax = timeout.tmax
        else:
            self.finite = timeout is not None and timeout >= 0
            self.tmax = time.time() + timeout if self.finite else None

    def expired(self):
        return self.finite and time.time() >= self.tmax

    def timeleft(self):
        return max((0, self.tmax - time.time())) if self.finite else None

    def sleep(self, interval):
        time.sleep(min(interval, self.timeleft()) if self.finite else interval)


def socket_backoff_connect(family, socktype, proto, addr, timeout, attempts):
    """connect will backoff if the response is not ready for a pseudo random number greater than zero and less than
        51e-6, 153e-6, 358e-6, 768e-6, 1587e-6, 3225e-6, 6502e-6, 13056e-6, 26163e-6, 52377e-6
    this should help avoid congestion.
    """
    sock = socket.socket(family, socktype, proto)
    collision = 0
    connecting = True
    while connecting:
        collision += 1
        try:
            sock.settimeout(timeout)
            sock.connect(addr)
            connecting = False
        except socket.timeout:
            if collision == attempts or attempts < 1:
                raise
            else:
                sock.close()
                sock = socket.socket(family, socktype, proto)
                time.sleep(exp_backoff(collision))
    return sock


def exp_backoff(collision):
    """ Exponential backoff algorithm from
    Peterson, L.L., and Davie, B.S. Computer Networks: a systems approach. 5th ed. pp. 127
    """
    n = min(collision, 10)
    supremum_adjustment = 1 if n > 3 else 0
    k = random.uniform(0, 2**n - supremum_adjustment)
    return k * 0.0000512


def get_id_pack(obj):
    """introspects the given "local" object, returns id_pack as expected by
    BaseNetref

    The given object is "local" in the sense that it is from the local
    cache. Any object in the local cache exists in the current address
    space or is a netref. A netref in the local cache could be from a
    chained-connection. To handle type related behavior properly, the
    attribute `__class__` is a descriptor for netrefs.

    So, check thy assumptions regarding the given object when creating
    `id_pack`.
    """
    undef = object()
    name_pack = getattr(obj, '____id_pack__', undef)
    if name_pack is not undef:
        return name_pack

    obj_name = getattr(obj, '__name__', None)
    if inspect.ismodule(obj):
        # Handle instances of the module class. Since inspect.ismodule(obj) is False,
        # the module class id pack must have zero for the instance object id.
        if inspect.ismodule(obj) and obj_name != 'module':
            if obj_name in sys.modules:
                name_pack = obj_name
            else:
                obj_cls = getattr(obj, '__class__', type(obj))
                name_pack = f'{obj_cls.__module__}.{obj_name}'
        elif inspect.ismodule(obj):
            name_pack = '{obj.__module__}.{obj_name}'
        else:
            obj_module = getattr(obj, '__module__', undef)
            if obj_module is not undef:
                name_pack = f'{obj.__module__}.{obj_name}'
            else:
                name_pack = obj_name
        return (name_pack, id(type(obj)), id(obj))

    if not inspect.isclass(obj):
        obj_cls = getattr(obj, '__class__', type(obj))
        name_pack = f'{obj_cls.__module__}.{obj_cls.__name__}'
        return (name_pack, id(type(obj)), id(obj))

    name_pack = f'{obj.__module__}.{obj_name}'
    return (name_pack, id(obj), 0)


def get_methods(obj_attrs, obj):
    """introspects the given (local) object, returning a list of all of its
    methods (going up the MRO).

    :param obj: any local (not proxy) python object

    :returns: a list of ``(method name, docstring)`` tuples of all the methods
              of the given object
    """
    methods = {}
    attrs = {}
    if isinstance(obj, type):
        # don't forget the darn metaclass
        mros = list(reversed(type(obj).__mro__)) + list(reversed(obj.__mro__))
    else:
        mros = reversed(type(obj).__mro__)
    for basecls in mros:
        attrs.update(basecls.__dict__)
    for name, attr in attrs.items():
        if name not in obj_attrs and inspect.isroutine(attr):
            methods[name] = inspect.getdoc(attr)
    return methods.items()
