"""
rpyc connection factories
"""
import socket
import thread, threading
from rpyc import Connection, Channel, SocketStream, TunneledSocketStream, PipeStream, VoidService
from rpyc.utils.registry import UDPRegistryClient
from rpyc.lib import safe_import
ssl = safe_import("ssl")


class DiscoveryError(Exception):
    pass


#------------------------------------------------------------------------------
# API
#------------------------------------------------------------------------------
def connect_channel(channel, service = VoidService, config = {}):
    """creates a connection over a given channel
    channel - the channel to use
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    return Connection(service, channel, config = config)

def connect_stream(stream, service = VoidService, config = {}):
    """creates a connection over a given stream
    stream - the stream to use
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    return connect_channel(Channel(stream), service = service, config = config)

def connect_pipes(input, output, service = VoidService, config = {}):
    """creates a connection over the given input/output pipes
    input - the input pipe
    output - the output pipe
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    return connect_stream(PipeStream(input, output), service = service, config = config)

def connect_stdpipes(service = VoidService, config = {}):
    """creates a connection over the standard input/output pipes
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    return connect_stream(PipeStream.from_std(), service = service, config = config)

def connect(host, port, service = VoidService, config = {}):
    """creates a socket-connection to the given host
    host - the hostname to connect to
    port - the TCP port to use
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    return Connection(service, Channel(SocketStream.connect(host, port)), config = config)

def tlslite_connect(host, port, username, password, service = VoidService, config = {}):
    """creates a TLS-connection to the given host (encrypted and authenticated)
    username - the username used to authenticate the client
    password - the password used to authenticate the client
    host - the hostname to connect to
    port - the TCP port to use
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    s = SocketStream.tlslite_connect(host, port, username, password)
    return Connection(service, Channel(s), config = config)

def ssl_connect(host, port, keyfile = None, certfile = None, ca_certs = None,
        ssl_version = None, service = VoidService, config = {}):
    """creates an SSL-wrapped connection to the given host (encrypted and
    authenticated).
    host - the hostname to connect to
    port - the TCP port to use
    service - the local service to expose (defaults to Void)
    config - configuration dict

    keyfile, certfile, ca_certs, ssl_version -- arguments to ssl.wrap_socket.
    see that module's documentation for further info."""
    kwargs = {"server_side" : False}
    if keyfile:
        kwargs["keyfile"] = keyfile
    if certfile:
        kwargs["certfile"] = certfile
    if ca_certs:
        kwargs["ca_certs"] = ca_certs
    if ssl_version:
        kwargs["ssl_version"] = ssl_version
    else:
        kwargs["ssl_version"] = ssl.PROTOCOL_TLSv1
    s = SocketStream.ssl_connect(host, port, kwargs)
    return Connection(service, Channel(s), config = config)

def _get_free_port():
    """attempts to find a free port"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    _, port = s.getsockname()
    s.close()
    return port

def ssh_connect(sshctx, remote_port, service = VoidService, config = {}):
    """connects to an rpyc server over an SSH tunnel
    sshctx - an rpyc.utils.ssh.SshContext object
    remote_port - the port of the remote server
    service - the local service to expose (defaults to Void)
    config - configuration dict
    """
    loc_port = _get_free_port()
    tun = sshctx.tunnel(loc_port, remote_port)
    stream = TunneledSocketStream.connect("localhost", loc_port)
    stream.tun = tun
    return Connection(service, Channel(stream), config = config)

def discover(service_name, host = None, registrar = None, timeout = 2):
    """discovers hosts running the given service
    service_name - the service to look for
    host - limit the discovery to the given host only (None means any host)
    registrar - use this registry client to discover services. if None,
      use the default UDPRegistryClient with the default settings.
    timeout - the number of seconds to wait for a reply from the registry
    if no hosts are found, raises DiscoveryError
    returns a list of (ip, port) pairs
    """
    if registrar is None:
        registrar = UDPRegistryClient(timeout = timeout)
    addrs = registrar.discover(service_name)
    if not addrs:
        raise DiscoveryError("no servers exposing %r were found" % (service_name,))
    if host:
        ips = socket.gethostbyname_ex(host)[2]
        addrs = [(h, p) for h, p in addrs if h in ips]
    if not addrs:
        raise DiscoveryError("no servers exposing %r were found on %r" % (service_name, host))
    return addrs

def connect_by_service(service_name, host = None, service = VoidService, config = {}):
    """create a connection to an arbitrary server that exposes the requested service
    service_name - the service to discover
    host - limit discovery to the given host only (None means any host)
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    host, port = discover(service_name, host = host)[0]
    return connect(host, port, service, config = config)

def connect_subproc(args, service = VoidService, config = {}):
    """runs an rpyc server on a child process that and connects to it over
    the stdio pipes. uses the subprocess module.
    args - the args to Popen, e.g., ["python", "-u", "myfile.py"]
    service - the local service to expose (defaults to Void)
    config - configuration dict"""
    from subprocess import Popen, PIPE
    proc = Popen(args, stdin = PIPE, stdout = PIPE)
    conn = connect_pipes(proc.stdout, proc.stdin, service = service, config = config)
    conn.proc = proc # just so you can have control over the processs
    return conn

def connect_thread(service = VoidService, config = {}, remote_service = VoidService, remote_config = {}):
    """starts an rpyc server on a thread and connects to it over a socket.
    service - the local service to expose (defaults to Void)
    config - configuration dict
    server_service - the remote service to expose (of the server; defaults to Void)
    server_config - remote configuration dict (of the server)
    """
    listener = socket.socket()
    listener.bind(("localhost", 0))
    listener.listen(1)

    def server(listener = listener):
        client = listener.accept()[0]
        listener.close()
        conn = connect_stream(SocketStream(client), service = remote_service,
            config = remote_config)
        try:
            conn.serve_all()
        except KeyboardInterrupt:
            thread.interrupt_main()

    t = threading.Thread(target = server)
    t.setDaemon(True)
    t.start()
    host, port = listener.getsockname()
    return connect(host, port, service = service, config = config)

