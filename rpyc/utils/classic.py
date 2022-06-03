from __future__ import with_statement
import sys
import os
import inspect
from rpyc.lib.compat import pickle, execute
from rpyc.core.service import ClassicService, Slave
from rpyc.utils import factory
from rpyc.core.service import ModuleNamespace  # noqa: F401
from rpyc.core.consts import STREAM_CHUNK
from contextlib import contextmanager


DEFAULT_SERVER_PORT = 18812
DEFAULT_SERVER_SSL_PORT = 18821

SlaveService = ClassicService   # avoid renaming SlaveService in this module for now

# ===============================================================================
# connecting
# ===============================================================================


def connect_channel(channel):
    """
    Creates an RPyC connection over the given ``channel``

    :param channel: the :class:`rpyc.core.channel.Channel` instance

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect_channel(channel, SlaveService)


def connect_stream(stream):
    """
    Creates an RPyC connection over the given stream

    :param channel: the :class:`rpyc.core.stream.Stream` instance

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect_stream(stream, SlaveService)


def connect_stdpipes():
    """
    Creates an RPyC connection over the standard pipes (``stdin`` and ``stdout``)

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect_stdpipes(SlaveService)


def connect_pipes(input, output):
    """
    Creates an RPyC connection over two pipes

    :param input: the input pipe
    :param output: the output pipe

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect_pipes(input, output, SlaveService)


def connect(host, port=DEFAULT_SERVER_PORT, ipv6=False, keepalive=False):
    """
    Creates a socket connection to the given host and port.

    :param host: the host to connect to
    :param port: the TCP port
    :param ipv6: whether to create an IPv6 socket or IPv4

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect(host, port, SlaveService, ipv6=ipv6, keepalive=keepalive)


def unix_connect(path):
    """
    Creates a socket connection to the given host and port.

    :param path: the path to the unix domain socket

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.unix_connect(path, SlaveService)


def ssl_connect(host, port=DEFAULT_SERVER_SSL_PORT, keyfile=None,
                certfile=None, ca_certs=None, cert_reqs=None, ssl_version=None,
                ciphers=None, ipv6=False):
    """Creates a secure (``SSL``) socket connection to the given host and port,
    authenticating with the given certfile and CA file.

    :param host: the host to connect to
    :param port: the TCP port to use
    :param ipv6: whether to create an IPv6 socket or an IPv4 one

    The following arguments are passed to
    `ssl.SSLContext <http://docs.python.org/dev/library/ssl.html#ssl.SSLContext>`_ and
    its corresponding methods:

    :param keyfile: see ``ssl.SSLContext.load_cert_chain``. May be ``None``
    :param certfile: see ``ssl.SSLContext.load_cert_chain``. May be ``None``
    :param ca_certs: see ``ssl.SSLContext.load_verify_locations``. May be ``None``
    :param cert_reqs: see ``ssl.SSLContext.verify_mode``. By default, if ``ca_cert`` is
                      specified, the requirement is set to ``CERT_REQUIRED``; otherwise
                      it is set to ``CERT_NONE``
    :param ssl_version: see ``ssl.SSLContext``. The default is defined by
                        ``ssl.create_default_context``
    :param ciphers: see ``ssl.SSLContext.set_ciphers``. May be ``None``. New in
                    Python 2.7/3.2

    :returns: an RPyC connection exposing ``SlaveService``

    .. _wrap_socket:
    """
    return factory.ssl_connect(host, port, keyfile=keyfile, certfile=certfile,
                               ssl_version=ssl_version, ca_certs=ca_certs, service=SlaveService,
                               ipv6=ipv6)


def ssh_connect(remote_machine, remote_port):
    """Connects to the remote server over an SSH tunnel. See
    :func:`rpyc.utils.factory.ssh_connect` for more info.

    :param remote_machine: the :class:`plumbum.remote.RemoteMachine` instance
    :param remote_port: the remote TCP port

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.ssh_connect(remote_machine, remote_port, SlaveService)


def connect_subproc(server_file=None):
    """Runs an RPyC classic server as a subprocess and returns an RPyC
    connection to it over stdio

    :param server_file: The full path to the server script (``rpyc_classic.py``).
                        If not given, ``which rpyc_classic.py`` will be attempted.

    :returns: an RPyC connection exposing ``SlaveService``
    """
    if server_file is None:
        server_file = os.popen("which rpyc_classic.py").read().strip()
        if not server_file:
            raise ValueError("server_file not given and could not be inferred")
    return factory.connect_subproc([sys.executable, "-u", server_file, "-q", "-m", "stdio"],
                                   SlaveService)


def connect_thread():
    """
    Starts a SlaveService on a thread and connects to it. Useful for testing
    purposes. See :func:`rpyc.utils.factory.connect_thread`

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect_thread(SlaveService, remote_service=SlaveService)


def connect_multiprocess(args={}):
    """
    Starts a SlaveService on a multiprocess process and connects to it.
    Useful for testing purposes and running multicore code thats uses shared
    memory. See :func:`rpyc.utils.factory.connect_multiprocess`

    :returns: an RPyC connection exposing ``SlaveService``
    """
    return factory.connect_multiprocess(SlaveService, remote_service=SlaveService, args=args)


# ===============================================================================
# remoting utilities
# ===============================================================================

def upload(conn, localpath, remotepath, filter=None, ignore_invalid=False, chunk_size=STREAM_CHUNK):
    """uploads a file or a directory to the given remote path

    :param localpath: the local file or directory
    :param remotepath: the remote path
    :param filter: a predicate that accepts the filename and determines whether
                   it should be uploaded; None means any file
    :param chunk_size: the IO chunk size
    """
    if os.path.isdir(localpath):
        upload_dir(conn, localpath, remotepath, filter, chunk_size)
    elif os.path.isfile(localpath):
        upload_file(conn, localpath, remotepath, chunk_size)
    else:
        if not ignore_invalid:
            raise ValueError(f"cannot upload {localpath!r}")


def upload_file(conn, localpath, remotepath, chunk_size=STREAM_CHUNK):
    with open(localpath, "rb") as lf:
        with conn.builtin.open(remotepath, "wb") as rf:
            while True:
                buf = lf.read(chunk_size)
                if not buf:
                    break
                rf.write(buf)


def upload_dir(conn, localpath, remotepath, filter=None, chunk_size=STREAM_CHUNK):
    if not conn.modules.os.path.isdir(remotepath):
        conn.modules.os.makedirs(remotepath)
    for fn in os.listdir(localpath):
        if not filter or filter(fn):
            lfn = os.path.join(localpath, fn)
            rfn = conn.modules.os.path.join(remotepath, fn)
            upload(conn, lfn, rfn, filter=filter, ignore_invalid=True, chunk_size=chunk_size)


def download(conn, remotepath, localpath, filter=None, ignore_invalid=False, chunk_size=STREAM_CHUNK):
    """
    download a file or a directory to the given remote path

    :param localpath: the local file or directory
    :param remotepath: the remote path
    :param filter: a predicate that accepts the filename and determines whether
                   it should be downloaded; None means any file
    :param chunk_size: the IO chunk size
    """
    if conn.modules.os.path.isdir(remotepath):
        download_dir(conn, remotepath, localpath, filter, chunk_size)
    elif conn.modules.os.path.isfile(remotepath):
        download_file(conn, remotepath, localpath, chunk_size)
    else:
        if not ignore_invalid:
            raise ValueError(f"cannot download {remotepath!r}")


def download_file(conn, remotepath, localpath, chunk_size=STREAM_CHUNK):
    with conn.builtin.open(remotepath, "rb") as rf:
        with open(localpath, "wb") as lf:
            while True:
                buf = rf.read(chunk_size)
                if not buf:
                    break
                lf.write(buf)


def download_dir(conn, remotepath, localpath, filter=None, chunk_size=STREAM_CHUNK):
    if not os.path.isdir(localpath):
        os.makedirs(localpath)
    for fn in conn.modules.os.listdir(remotepath):
        if not filter or filter(fn):
            rfn = conn.modules.os.path.join(remotepath, fn)
            lfn = os.path.join(localpath, fn)
            download(conn, rfn, lfn, filter=filter, ignore_invalid=True, chunk_size=chunk_size)


def upload_package(conn, module, remotepath=None, chunk_size=STREAM_CHUNK):
    """
    uploads a module or a package to the remote party

    :param conn: the RPyC connection to use
    :param module: the local module/package object to upload
    :param remotepath: the remote path (if ``None``, will default to the
                       remote system's python library (as reported by
                       ``distutils``)
    :param chunk_size: the IO chunk size

    .. note:: ``upload_module`` is just an alias to ``upload_package``

    example::

       import foo.bar
       ...
       rpyc.classic.upload_package(conn, foo.bar)

    """
    if remotepath is None:
        site = conn.modules["distutils.sysconfig"].get_python_lib()
        remotepath = conn.modules.os.path.join(site, module.__name__)
    localpath = os.path.dirname(os.path.abspath(inspect.getsourcefile(module)))
    upload(conn, localpath, remotepath, chunk_size=chunk_size)


upload_module = upload_package


def obtain(proxy):
    """obtains (copies) a remote object from a proxy object. the object is
    ``pickled`` on the remote side and ``unpickled`` locally, thus moved
    **by value**. changes made to the local object will not reflect remotely.

    :param proxy: an RPyC proxy object

    .. note:: the remote object to must be ``pickle``-able

    :returns: a copy of the remote object
    """
    return pickle.loads(pickle.dumps(proxy))


def deliver(conn, localobj):
    """delivers (recreates) a local object on the other party. the object is
    ``pickled`` locally and ``unpickled`` on the remote side, thus moved
    **by value**. changes made to the remote object will not reflect locally.

    :param conn: the RPyC connection
    :param localobj: the local object to deliver

    .. note:: the object must be ``picklable``

    :returns: a proxy to the remote object
    """
    # bytes-cast needed for IronPython-to-CPython communication, see #251:
    return conn.modules["rpyc.lib.compat"].pickle.loads(
        bytes(pickle.dumps(localobj)))


@contextmanager
def redirected_stdio(conn):
    r"""
    Redirects the other party's ``stdin``, ``stdout`` and ``stderr`` to
    those of the local party, so remote IO will occur locally.

    Example usage::

        with redirected_stdio(conn):
            conn.modules.sys.stdout.write("hello\n")   # will be printed locally

    """
    orig_stdin = conn.modules.sys.stdin
    orig_stdout = conn.modules.sys.stdout
    orig_stderr = conn.modules.sys.stderr
    try:
        conn.modules.sys.stdin = sys.stdin
        conn.modules.sys.stdout = sys.stdout
        conn.modules.sys.stderr = sys.stderr
        yield
    finally:
        conn.modules.sys.stdin = orig_stdin
        conn.modules.sys.stdout = orig_stdout
        conn.modules.sys.stderr = orig_stderr


def pm(conn):
    """same as ``pdb.pm()`` but on a remote exception

    :param conn: the RPyC connection
    """
    # pdb.post_mortem(conn.root.getconn()._last_traceback)
    with redirected_stdio(conn):
        conn.modules.pdb.post_mortem(conn.root.getconn()._last_traceback)


def interact(conn, namespace=None):
    """remote interactive interpreter

    :param conn: the RPyC connection
    :param namespace: the namespace to use (a ``dict``)
    """
    if namespace is None:
        namespace = {}
    namespace["conn"] = conn
    with redirected_stdio(conn):
        conn.execute("""def _rinteract(ns):
            import code
            code.interact(local = dict(ns))""")
        conn.namespace["_rinteract"](namespace)


class MockClassicConnection(object):
    """Mock classic RPyC connection object. Useful when you want the same code to run remotely or locally.
    """

    def __init__(self):
        self.root = Slave()
        ClassicService._install(self, self.root)


def teleport_function(conn, func, globals=None, def_=True):
    """
    "Teleports" a function (including nested functions/closures) over the RPyC connection.
    The function is passed in bytecode form and reconstructed on the other side.

    The function cannot have non-brinable defaults (e.g., ``def f(x, y=[8]):``,
    since a ``list`` isn't brinable), or make use of non-builtin globals (like modules).
    You can overcome the second restriction by moving the necessary imports into the
    function body, e.g. ::

        def f(x, y):
            import os
            return (os.getpid() + y) * x

    .. note:: While it is not forbidden to "teleport" functions across different Python
              versions, it *may* result in errors due to Python bytecode differences. It is
              recommended to ensure both the client and the server are of the same Python
              version when using this function.

    :param conn: the RPyC connection
    :param func: the function object to be delivered to the other party
    """
    if globals is None:
        globals = conn.namespace
    from rpyc.utils.teleportation import export_function
    exported = export_function(func)
    return conn.modules["rpyc.utils.teleportation"].import_function(
        exported, globals, def_)
