"""
RPyC connection factories: ease the creation of a connection for the common
cases)
"""
from __future__ import with_statement
import socket
from contextlib import closing
from functools import partial
import threading
try:
    from thread import interrupt_main
except ImportError:
    try:
        from _thread import interrupt_main
    except ImportError:
        # assume jython (#83)
        from java.lang import System
        interrupt_main = System.exit

from rpyc.core.channel import Channel
from rpyc.core.stream import SocketStream, TunneledSocketStream, PipeStream
from rpyc.core.service import VoidService, MasterService, SlaveService
from rpyc.utils.registry import UDPRegistryClient
from rpyc.lib import safe_import, spawn
ssl = safe_import("ssl")


class DiscoveryError(Exception):
    pass


class ForbiddenError(Exception):
    pass


# ------------------------------------------------------------------------------
# API
# ------------------------------------------------------------------------------
def connect_channel(channel, service=VoidService, config={}):
    """creates a connection over a given channel

    :param channel: the channel to use
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :returns: an RPyC connection
    """
    return service._connect(channel, config)


def connect_stream(stream, service=VoidService, config={}):
    """creates a connection over a given stream

    :param stream: the stream to use
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :returns: an RPyC connection
    """
    return connect_channel(Channel(stream), service=service, config=config)


def connect_pipes(input, output, service=VoidService, config={}):
    """
    creates a connection over the given input/output pipes

    :param input: the input pipe
    :param output: the output pipe
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :returns: an RPyC connection
    """
    return connect_stream(PipeStream(input, output), service=service, config=config)


def connect_stdpipes(service=VoidService, config={}):
    """
    creates a connection over the standard input/output pipes

    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :returns: an RPyC connection
    """
    return connect_stream(PipeStream.from_std(), service=service, config=config)


def connect(host, port, service=VoidService, config={}, ipv6=False, keepalive=False):
    """
    creates a socket-connection to the given host and port

    :param host: the hostname to connect to
    :param port: the TCP port to use
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict
    :param ipv6: whether to create an IPv6 socket (defaults to ``False``)
    :param keepalive: whether to set TCP keepalive on the socket (defaults to ``False``)

    :returns: an RPyC connection
    """
    s = SocketStream.connect(host, port, ipv6=ipv6, keepalive=keepalive)
    return connect_stream(s, service, config)


def unix_connect(path, service=VoidService, config={}):
    """
    creates a socket-connection to the given unix domain socket

    :param path: the path to the unix domain socket
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :returns: an RPyC connection
    """
    s = SocketStream.unix_connect(path)
    return connect_stream(s, service, config)


def ssl_connect(host, port, keyfile=None, certfile=None, ca_certs=None,
                cert_reqs=None, ssl_version=None, ciphers=None,
                service=VoidService, config={}, ipv6=False, keepalive=False, verify_mode=None):
    """
    creates an SSL-wrapped connection to the given host (encrypted and
    authenticated).

    :param host: the hostname to connect to
    :param port: the TCP port to use
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict
    :param ipv6: whether to create an IPv6 socket or an IPv4 one(defaults to ``False``)
    :param keepalive: whether to set TCP keepalive on the socket (defaults to ``False``)

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
    :param verify_mode: see ``ssl.SSLContext.verify_mode``

    :returns: an RPyC connection
    """
    ssl_kwargs = {"server_side": False}
    if keyfile is not None:
        ssl_kwargs["keyfile"] = keyfile
    if certfile is not None:
        ssl_kwargs["certfile"] = certfile
    if verify_mode is not None:
        ssl_kwargs["cert_reqs"] = verify_mode
    else:
        ssl_kwargs["cert_reqs"] = ssl.CERT_NONE
    if ca_certs is not None:
        ssl_kwargs["ca_certs"] = ca_certs
        ssl_kwargs["cert_reqs"] = ssl.CERT_REQUIRED
    if cert_reqs is not None:
        ssl_kwargs["cert_reqs"] = cert_reqs
    elif cert_reqs != ssl.CERT_NONE:
        ssl_kwargs["check_hostname"] = False
    if ssl_version is not None:
        ssl_kwargs["ssl_version"] = ssl_version
    if ciphers is not None:
        ssl_kwargs["ciphers"] = ciphers
    s = SocketStream.ssl_connect(host, port, ssl_kwargs, ipv6=ipv6, keepalive=keepalive)
    return connect_stream(s, service, config)


def _get_free_port():
    """attempts to find a free port"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with closing(s):
        s.bind(("localhost", 0))
        return s.getsockname()[1]


_ssh_connect_lock = threading.Lock()


def ssh_connect(remote_machine, remote_port, service=VoidService, config={}):
    """
    Connects to an RPyC server over an SSH tunnel (created by plumbum).
    See `Plumbum tunneling <http://plumbum.readthedocs.org/en/latest/remote.html#tunneling>`_
    for further details.

    .. note::
       This function attempts to allocate a free TCP port for the underlying tunnel, but doing
       so is inherently prone to a race condition with other processes who might bind the
       same port before sshd does. Albeit unlikely, there is no sure way around it.

    :param remote_machine: an :class:`plumbum.remote.RemoteMachine` instance
    :param remote_port: the port of the remote server
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :returns: an RPyC connection
    """
    with _ssh_connect_lock:
        loc_port = _get_free_port()
        tun = remote_machine.tunnel(loc_port, remote_port)
        stream = TunneledSocketStream.connect("localhost", loc_port)
        stream.tun = tun
    return service._connect(Channel(stream), config=config)


def discover(service_name, host=None, registrar=None, timeout=2):
    """
    discovers hosts running the given service

    :param service_name: the service to look for
    :param host: limit the discovery to the given host only (None means any host)
    :param registrar: use this registry client to discover services. if None,
                      use the default UDPRegistryClient with the default settings.
    :param timeout: the number of seconds to wait for a reply from the registry
                    if no hosts are found, raises DiscoveryError

    :raises: ``DiscoveryError`` if no server is found
    :returns: a list of (ip, port) pairs
    """
    if registrar is None:
        registrar = UDPRegistryClient(timeout=timeout)
    addrs = registrar.discover(service_name)
    if not addrs:
        raise DiscoveryError(f"no servers exposing {service_name!r} were found")
    if host:
        ips = socket.gethostbyname_ex(host)[2]
        addrs = [(h, p) for h, p in addrs if h in ips]
    if not addrs:
        raise DiscoveryError(f"no servers exposing {service_name} were found on {host}")
    return addrs


def list_services(registrar=None, filter_host=None, timeout=2):
    services = ()
    if registrar is None:
        registrar = UDPRegistryClient(timeout=timeout)
    services = registrar.list(filter_host)
    if services is None:
        raise ForbiddenError("Registry doesn't allow listing")
    return services


def connect_by_service(service_name, host=None, registrar=None, timeout=2, service=VoidService, config={}):
    """create a connection to an arbitrary server that exposes the requested service

    :param service_name: the service to discover
    :param host: limit discovery to the given host only (None means any host)
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict

    :raises: ``DiscoveryError`` if no server is found
    :returns: an RPyC connection
    """
    # The registry server may have multiple services registered for the same service name,
    # some of which could be dead. We iterate over the list returned and return the first
    # one we could connect to. If none of the registered servers is responsive we re-throw
    # the exception
    addrs = discover(service_name, host=host, registrar=registrar, timeout=timeout)
    for host, port in addrs:
        try:
            return connect(host, port, service, config=config)
        except socket.error:
            pass
    raise DiscoveryError(f"All services are down: {addrs}")


def connect_subproc(args, service=VoidService, config={}):
    """runs an rpyc server on a child process that and connects to it over
    the stdio pipes. uses the subprocess module.

    :param args: the args to Popen, e.g., ["python", "-u", "myfile.py"]
    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict
    """
    from subprocess import Popen, PIPE
    proc = Popen(args, stdin=PIPE, stdout=PIPE)
    conn = connect_pipes(proc.stdout, proc.stdin, service=service, config=config)
    conn.proc = proc  # just so you can have control over the processs
    return conn


def _server(listener, remote_service, remote_config, args=None):
    try:
        with closing(listener):
            client = listener.accept()[0]
        conn = connect_stream(SocketStream(client), service=remote_service, config=remote_config)
        if isinstance(args, dict):
            _oldstyle = (MasterService, SlaveService)
            is_newstyle = isinstance(remote_service, type) and not issubclass(remote_service, _oldstyle)
            is_newstyle |= not isinstance(remote_service, type) and not isinstance(remote_service, _oldstyle)
            is_voidservice = isinstance(remote_service, type) and issubclass(remote_service, VoidService)
            is_voidservice |= not isinstance(remote_service, type) and isinstance(remote_service, VoidService)
            if is_newstyle and not is_voidservice:
                conn._local_root.exposed_namespace.update(args)
            elif not is_voidservice:
                conn._local_root.namespace.update(args)

        conn.serve_all()
    except KeyboardInterrupt:
        interrupt_main()


def connect_thread(service=VoidService, config={}, remote_service=VoidService, remote_config={}):
    """starts an rpyc server on a new thread, bound to an arbitrary port,
    and connects to it over a socket.

    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict
    :param remote_service: the remote service to expose (of the server; defaults to Void)
    :param remote_config: remote configuration dict (of the server)
    """
    listener = socket.socket()
    listener.bind(("localhost", 0))
    listener.listen(1)
    remote_server = partial(_server, listener, remote_service, remote_config)
    spawn(remote_server)
    host, port = listener.getsockname()
    return connect(host, port, service=service, config=config)


def connect_multiprocess(service=VoidService, config={}, remote_service=VoidService, remote_config={}, args={}):
    """starts an rpyc server on a new process, bound to an arbitrary port,
    and connects to it over a socket. Basically a copy of connect_thread().
    However if args is used and if these are shared memory then changes
    will be bi-directional. That is we now have access to shared memmory.

    :param service: the local service to expose (defaults to Void)
    :param config: configuration dict
    :param remote_service: the remote service to expose (of the server; defaults to Void)
    :param remote_config: remote configuration dict (of the server)
    :param args: dict of local vars to pass to new connection, form {'name':var}

    Contributed by *@tvanzyl*
    """
    from multiprocessing import Process

    listener = socket.socket()
    listener.bind(("localhost", 0))
    listener.listen(1)
    remote_server = partial(_server, listener, remote_service, remote_config, args)
    t = Process(target=remote_server)
    t.start()
    host, port = listener.getsockname()
    return connect(host, port, service=service, config=config)
