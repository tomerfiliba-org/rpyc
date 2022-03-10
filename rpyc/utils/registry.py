"""
RPyC Registry Server maintains service information on RPyC services for *Service Registry and Discovery patterns*. Service Registry and Discovery patterns solve the connectivity problem for communication between services and external consumers. RPyC services will register with the server when :code:`auto_register` is :code:`True`.

Service registries such as `Avahi <http://en.wikipedia.org/wiki/Avahi_(software)>`_ and
`Bonjour <http://en.wikipedia.org/wiki/Bonjour_(software)>`_ are alternatives to the RPyC Registry Server. These alternatives do no support Windows and have more restrictive licensing.

Refer to :file:`rpyc/scripts/rpyc_registry.py` for more info.
"""
import sys
import socket
import time
import logging
from contextlib import closing
from rpyc.core import brine


DEFAULT_PRUNING_TIMEOUT = 4 * 60
MAX_DGRAM_SIZE = 1500
REGISTRY_PORT = 18811


# ------------------------------------------------------------------------------
# servers
# ------------------------------------------------------------------------------

class RegistryServer(object):
    """Base registry server"""

    def __init__(self, listenersock, pruning_timeout=None, logger=None, allow_listing=False):
        self.sock = listenersock
        self.port = self.sock.getsockname()[1]
        self.active = False
        self.services = {}
        if pruning_timeout is None:
            pruning_timeout = DEFAULT_PRUNING_TIMEOUT
        self.pruning_timeout = pruning_timeout
        if logger is None:
            logger = self._get_logger()
        self.allow_listing = allow_listing
        self.logger = logger

    def _get_logger(self):
        raise NotImplementedError()

    def on_service_added(self, name, addrinfo):
        """called when a new service joins the registry (but not on keepalives).
        override this to add custom logic"""

    def on_service_removed(self, name, addrinfo):
        """called when a service unregisters or is pruned.
        override this to add custom logic"""

    def _add_service(self, name, addrinfo):
        """updates the service's keep-alive time stamp"""
        if name not in self.services:
            self.services[name] = {}
        is_new = addrinfo not in self.services[name]
        self.services[name][addrinfo] = time.time()
        if is_new:
            try:
                self.on_service_added(name, addrinfo)
            except Exception:
                self.logger.exception('error executing service add callback')

    def _remove_service(self, name, addrinfo):
        """removes a single server of the given service"""
        self.services[name].pop(addrinfo, None)
        if not self.services[name]:
            del self.services[name]
        try:
            self.on_service_removed(name, addrinfo)
        except Exception:
            self.logger.exception('error executing service remove callback')

    def cmd_query(self, host, name):
        """implementation of the ``query`` command"""
        name = name.upper()
        self.logger.debug(f"querying for {name!r}")
        if name not in self.services:
            self.logger.debug("no such service")
            return ()

        oldest = time.time() - self.pruning_timeout
        all_servers = sorted(self.services[name].items(), key=lambda x: x[1])
        servers = []
        for addrinfo, t in all_servers:
            if t < oldest:
                self.logger.debug(f"discarding stale {addrinfo[0]}:{addrinfo[1]}")
                self._remove_service(name, addrinfo)
            else:
                servers.append(addrinfo)

        self.logger.debug(f"replying with {servers!r}")
        return tuple(servers)

    def cmd_list(self, host, filter_host):
        """implementation for the ``list`` command"""
        self.logger.debug("querying for services list:")
        if not self.allow_listing:
            self.logger.debug("listing is disabled")
            return None
        services = []
        if filter_host[0]:
            for serv in self.services.keys():
                known_hosts = [h[0] for h in self.services[serv].keys()]
                if filter_host[0] in known_hosts:
                    services.append(serv)
            services = tuple(services)
        else:
            services = tuple(self.services.keys())
        self.logger.debug(f"replying with {services}")

        return services

    def cmd_register(self, host, names, port):
        """implementation of the ``register`` command"""
        self.logger.debug(f"registering {host}:{port} as {', '.join(names)}")
        for name in names:
            self._add_service(name.upper(), (host, port))
        return "OK"

    def cmd_unregister(self, host, port):
        """implementation of the ``unregister`` command"""
        self.logger.debug(f"unregistering {host}:{port}")
        for name in list(self.services.keys()):
            self._remove_service(name, (host, port))
        return "OK"

    def _recv(self):
        raise NotImplementedError()

    def _send(self, data, addrinfo):
        raise NotImplementedError()

    def _work(self):
        while self.active:
            try:
                data, addrinfo = self._recv()
            except (socket.error, socket.timeout):
                continue
            try:
                magic, cmd, args = brine.load(data)
            except Exception:
                continue
            if magic != "RPYC":
                self.logger.warn(f"invalid magic: {magic!r}")
                continue
            cmdfunc = getattr(self, f"cmd_{cmd.lower()}", None)
            if not cmdfunc:
                self.logger.warn(f"unknown command: {cmd!r}")
                continue

            try:
                reply = cmdfunc(addrinfo[0], *args)
            except Exception:
                self.logger.exception('error executing function')
            else:
                self._send(brine.dump(reply), addrinfo)

    def start(self):
        """Starts the registry server (blocks)"""
        if self.active:
            raise ValueError("server is already running")
        if self.sock is None:
            raise ValueError("object disposed")
        addrinfo = self.sock.getsockname()[:2]
        self.logger.debug(f"server started on {addrinfo[0]}:{addrinfo[1]}")
        try:
            self.active = True
            self._work()
        except KeyboardInterrupt:
            self.logger.warn("User interrupt!")
        finally:
            self.active = False
            self.logger.debug("server closed")
            self.sock.close()
            self.sock = None

    def close(self):
        """Closes (terminates) the registry server"""
        if not self.active:
            raise ValueError("server is not running")
        self.logger.debug("stopping server...")
        self.active = False


class UDPRegistryServer(RegistryServer):
    """UDP-based registry server. The server listens to UDP broadcasts and
    answers them. Useful in local networks, were broadcasts are allowed"""

    TIMEOUT = 1.0

    def __init__(self, host="0.0.0.0", port=REGISTRY_PORT, pruning_timeout=None, logger=None, allow_listing=False):
        family, socktype, proto, _, sockaddr = socket.getaddrinfo(host, port, 0,
                                                                  socket.SOCK_DGRAM)[0]
        sock = socket.socket(family, socktype, proto)
        sock.bind(sockaddr)
        sock.settimeout(self.TIMEOUT)
        RegistryServer.__init__(self, sock, pruning_timeout=pruning_timeout,
                                logger=logger, allow_listing=allow_listing)

    def _get_logger(self):
        return logging.getLogger(f"REGSRV/UDP/{self.port}")

    def _recv(self):
        return self.sock.recvfrom(MAX_DGRAM_SIZE)

    def _send(self, data, addrinfo):
        try:
            self.sock.sendto(data, addrinfo)
        except (socket.error, socket.timeout):
            pass


class TCPRegistryServer(RegistryServer):
    """TCP-based registry server. The server listens to a certain TCP port and
    answers requests. Useful when you need to cross routers in the network, since
    they block UDP broadcasts"""

    TIMEOUT = 3.0

    def __init__(self, host="0.0.0.0", port=REGISTRY_PORT, pruning_timeout=None,
                 logger=None, reuse_addr=True, allow_listing=False):

        family, socktype, proto, _, sockaddr = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)[0]
        sock = socket.socket(family, socktype, proto)
        if reuse_addr and sys.platform != "win32":
            # warning: reuseaddr is not what you expect on windows!
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(sockaddr)
        sock.listen(10)
        sock.settimeout(self.TIMEOUT)
        RegistryServer.__init__(self, sock, pruning_timeout=pruning_timeout,
                                logger=logger, allow_listing=allow_listing)
        self._connected_sockets = {}

    def _get_logger(self):
        return logging.getLogger(f"REGSRV/TCP/{self.port}")

    def _recv(self):
        sock2, _ = self.sock.accept()
        addrinfo = sock2.getpeername()
        data = sock2.recv(MAX_DGRAM_SIZE)
        self._connected_sockets[addrinfo] = sock2
        return data, addrinfo

    def _send(self, data, addrinfo):
        sock2 = self._connected_sockets.pop(addrinfo)
        with closing(sock2):
            try:
                sock2.send(data)
            except (socket.error, socket.timeout):
                pass

# ------------------------------------------------------------------------------
# clients (registrars)
# ------------------------------------------------------------------------------


class RegistryClient(object):
    """Base registry client. Also known as **registrar**"""

    REREGISTER_INTERVAL = 60

    def __init__(self, ip, port, timeout, logger=None):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        if logger is None:
            logger = self._get_logger()
        self.logger = logger

    def _get_logger(self):
        raise NotImplementedError()

    def discover(self, name):
        """Sends a query for the specified service name.

        :param name: the service name (or one of its aliases)

        :returns: a list of ``(host, port)`` tuples
        """
        raise NotImplementedError()

    def list(self, filter_host=None):
        """
        Send a query for the full lists of exposed servers
        :returns: a list of `` service_name ``
        """
        raise NotImplementedError()

    def register(self, aliases, port):
        """Registers the given service aliases with the given TCP port. This
        API is intended to be called only by an RPyC server.

        :param aliases: the :class:`service's <rpyc.core.service.Service>` aliases
        :param port: the listening TCP port of the server
        """
        raise NotImplementedError()

    def unregister(self, port):
        """Unregisters the given RPyC server. This API is intended to be called
        only by an RPyC server.

        :param port: the listening TCP port of the RPyC server to unregister
        """
        raise NotImplementedError()


class UDPRegistryClient(RegistryClient):
    """UDP-based registry clients. By default, it sends UDP broadcasts (requires
    special user privileges on certain OS's) and collects the replies. You can
    also specify the IP address to send to.

    Example::

        registrar = UDPRegistryClient()
        list_of_services = registrar.list()
        list_of_servers = registrar.discover("foo")

    .. note::
       Consider using :func:`rpyc.utils.factory.discover` instead
    """

    def __init__(self, ip="255.255.255.255", port=REGISTRY_PORT, timeout=2,
                 bcast=None, logger=None, ipv6=False):
        RegistryClient.__init__(self, ip=ip, port=port, timeout=timeout,
                                logger=logger)

        if ipv6:
            self.sock_family = socket.AF_INET6
            self.bcast = False
        else:
            self.sock_family = socket.AF_INET
            if bcast is None:
                bcast = "255" in ip.split(".")
            self.bcast = bcast

    def _get_logger(self):
        return logging.getLogger('REGCLNT/UDP')

    def discover(self, name):
        sock = socket.socket(self.sock_family, socket.SOCK_DGRAM)

        with closing(sock):
            if self.bcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            data = brine.dump(("RPYC", "QUERY", (name,)))
            sock.sendto(data, (self.ip, self.port))
            sock.settimeout(self.timeout)

            try:
                data, _ = sock.recvfrom(MAX_DGRAM_SIZE)
            except (socket.error, socket.timeout):
                servers = ()
            else:
                servers = brine.load(data)
        return servers

    def list(self, filter_host=None):
        sock = socket.socket(self.sock_family, socket.SOCK_DGRAM)

        with closing(sock):
            if self.bcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            data = brine.dump(("RPYC", "LIST", ((filter_host,),)))
            sock.sendto(data, (self.ip, self.port))
            sock.settimeout(self.timeout)

            try:
                data, _ = sock.recvfrom(MAX_DGRAM_SIZE * 10)
            except (socket.error, socket.timeout):
                services = ()
            else:
                services = brine.load(data)
        return services

    def register(self, aliases, port, interface=""):
        self.logger.info(f"registering on {self.ip}:{self.port}")
        sock = socket.socket(self.sock_family, socket.SOCK_DGRAM)
        with closing(sock):
            sock.bind((interface, 0))
            if self.bcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            data = brine.dump(("RPYC", "REGISTER", (aliases, port)))
            sock.sendto(data, (self.ip, self.port))

            tmax = time.time() + self.timeout
            while time.time() < tmax:
                sock.settimeout(tmax - time.time())
                try:
                    data, address = sock.recvfrom(MAX_DGRAM_SIZE)
                    rip, rport = address[:2]
                except socket.timeout:
                    self.logger.warn("no registry acknowledged")
                    return False
                if rport != self.port:
                    continue
                try:
                    reply = brine.load(data)
                except Exception:
                    continue
                if reply == "OK":
                    self.logger.info(f"registry {rip}:{rport} acknowledged")
                    return True
            else:
                self.logger.warn("no registry acknowledged")
                return False

    def unregister(self, port):
        self.logger.info(f"unregistering from {self.ip}:{self.port}")
        sock = socket.socket(self.sock_family, socket.SOCK_DGRAM)
        with closing(sock):
            if self.bcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            data = brine.dump(("RPYC", "UNREGISTER", (port,)))
            sock.sendto(data, (self.ip, self.port))


class TCPRegistryClient(RegistryClient):
    """TCP-based registry client. You must specify the host (registry server)
    to connect to.

    Example::

        registrar = TCPRegistryClient("localhost")
        list_of_services = registrar.list()
        list_of_servers = registrar.discover("foo")

    .. note::
       Consider using :func:`rpyc.utils.factory.discover` instead
    """

    def __init__(self, ip, port=REGISTRY_PORT, timeout=2, logger=None):
        RegistryClient.__init__(self, ip=ip, port=port, timeout=timeout,
                                logger=logger)

    def _get_logger(self):
        return logging.getLogger('REGCLNT/TCP')

    def discover(self, name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with closing(sock):
            sock.settimeout(self.timeout)
            data = brine.dump(("RPYC", "QUERY", (name,)))
            sock.connect((self.ip, self.port))
            sock.send(data)

            try:
                data = sock.recv(MAX_DGRAM_SIZE)
            except (socket.error, socket.timeout):
                servers = ()
            else:
                servers = brine.load(data)
        return servers

    def list(self, filter_host=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with closing(sock):
            sock.settimeout(self.timeout)
            data = brine.dump(("RPYC", "LIST", ((filter_host,),)))
            sock.connect((self.ip, self.port))
            sock.send(data)

            try:
                data = sock.recv(MAX_DGRAM_SIZE)
            except (socket.error, socket.timeout):
                servers = ()
            else:
                servers = brine.load(data)
        return servers

    def register(self, aliases, port, interface=""):
        self.logger.info(f"registering on {self.ip}:{self.port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with closing(sock):
            sock.bind((interface, 0))
            sock.settimeout(self.timeout)
            data = brine.dump(("RPYC", "REGISTER", (aliases, port)))
            try:
                sock.connect((self.ip, self.port))
                sock.send(data)
            except (socket.error, socket.timeout):
                self.logger.warn("could not connect to registry")
                return False
            try:
                data = sock.recv(MAX_DGRAM_SIZE)
            except socket.timeout:
                self.logger.warn("registry did not acknowledge")
                return False
            try:
                reply = brine.load(data)
            except Exception:
                self.logger.warn("received corrupted data from registry")
                return False
            if reply == "OK":
                self.logger.info(f"registry {self.ip}:{self.port} acknowledged")

            return True

    def unregister(self, port):
        self.logger.info(f"unregistering from {self.ip}:{self.port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with closing(sock):
            sock.settimeout(self.timeout)
            data = brine.dump(("RPYC", "UNREGISTER", (port,)))
            try:
                sock.connect((self.ip, self.port))
                sock.send(data)
            except (socket.error, socket.timeout):
                self.logger.warn("could not connect to registry")
