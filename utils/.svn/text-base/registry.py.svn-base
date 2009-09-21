"""
rpyc registry server implementation
"""
import socket
import time
from rpyc.core.consts import REGISTRY_UDP_PORT
from rpyc.core import brine 
from rpyc.utils.logger import Logger


REGISTRY_KEEPALIVE_TIMEOUT = 4 * 60
MAX_DGRAM_SIZE = 1500


class RegistryServer(object):
    def __init__(self, host = "0.0.0.0", port = REGISTRY_UDP_PORT):
        self._active = False
        self.services = {}
        self.logger = Logger("REGSRV")
    
    def cmd_query(self, host, name):
        self.logger.debug("querying for %r", name)
        if name not in self.services:
            self.logger.debug("no such service")
            return ()
        
        oldest = time.time() - REGISTRY_KEEPALIVE_TIMEOUT
        all_servers = sorted(self.services[name].items(), key = lambda x: x[1])
        servers = []
        for addrinfo, t in all_servers:
            if t < oldest:
                self.logger.debug("discarding stale %s:%s", *addrinfo)
                del self.services[name][addrinfo]
                if not self.services[name]:
                    del self.services[name]
            else:
                servers.append(addrinfo)
        
        self.logger.debug("replying with %r", servers)
        return tuple(servers)
    
    def cmd_register(self, host, names, port):
        self.logger.debug("registering %s:%s as %s", host, port, ", ".join(names))
        t0 = time.time()
        for name in names:
            if name not in self.services:
                self.services[name] = {}
            self.services[name][host, port] = t0
        return "OK"
    
    def cmd_unregister(self, host, port):
        self.logger.debug("unregistering %s:%s", host, port)
        for name in self.services.keys():
            self.services[name].pop((host, port))
            if not self.services[name]:
                del self.services[name]
        return "OK"
    
    def _work(self, sock):
        while self._active:
            try:
                data, addrinfo = sock.recvfrom(MAX_DGRAM_SIZE)
            except (socket.error, socket.timeout):
                continue
            try:
                magic, cmd, args = brine.load(data)
            except:
                continue
            if magic != "RPYC":
                self.logger.warn("invalid magic: %r", magic)
                continue
            cmdfunc = getattr(self, "cmd_%s" % (cmd.lower(),), None)
            if not cmdfunc:
                self.logger.warn("unknown command: %r", cmd)
                continue
            
            host = addrinfo[0]
            try:
                reply = cmdfunc(host, *args)
            except Exception:
                self.logger.traceback()
                reply = None
            sock.sendto(brine.dump(reply), addrinfo)
    
    def start(self, poll_interval = 0.5):
        if self._active:
            raise ValueError("server is already running")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", REGISTRY_UDP_PORT))
        sock.settimeout(poll_interval)
        self.logger.debug("server started on %s:%s", *sock.getsockname())
        try:
            try:
                self.services.clear()
                self._active = True
                self._work(sock)
            except KeyboardInterrupt:
                self.logger.warn("User interrupt!")
        finally:
            self._active = False
            self.logger.debug("server closed")
            sock.close()
    
    def stop(self):
        if not self._active:
            raise ValueError("server is not running")
        self.logger.debug("stopping server...")
        self._active = False


# it's a singleton
RegistryServer = RegistryServer()


def discover_service(name, ip = "255.255.255.255", timeout = 2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    data = brine.dump(("RPYC", "QUERY", (name,)))
    sock.sendto(data, (ip, REGISTRY_UDP_PORT))
    
    sock.settimeout(timeout)
    try:
        try:
            data, addrinfo = sock.recvfrom(1500)
        except (socket.error, socket.timeout):
            servers = ()
        else:
            servers = brine.load(data)
    finally:
        sock.close()
    return servers





