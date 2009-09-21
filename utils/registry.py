"""
rpyc registry server implementation
"""
import sys
import socket
import time
from rpyc.core.consts import REGISTRY_UDP_PORT
from rpyc.core import brine 
from rpyc.utils.logger import Logger


KEEPALIVE_TIMEOUT = 4 * 60
MAX_DGRAM_SIZE = 1500


class RegistryServer(object):
    def __init__(self, host = "0.0.0.0", port = REGISTRY_UDP_PORT, 
    keepalive_timeout = KEEPALIVE_TIMEOUT, logger = None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.settimeout(0.1)
        self.active = False
        self.keepalive_timeout = keepalive_timeout
        self.services = {}
        if logger is None:
            self.logger = Logger("REGSRV")
    
    def on_service_added(self, name, addrinfo):
        """called when a new service joins the registry (but on keepalives).
        override this to add custom logic"""
    
    def on_service_removed(self, name, addrinfo):
        """called when a service unregisters or is pruned. 
        override this to add custom logic"""
    
    def add_service(self, name, addrinfo):
        if name not in self.services:
            self.services[name] = {}
        is_new = addrinfo not in self.services
        self.services[name][addrinfo] = time.time()
        if is_new:
            try:
                self.on_service_added(name, addrinfo)
            except Exception:
                self.logger.traceback()
    
    def remove_service(self, name, addrinfo):
        self.services[name].pop(addrinfo, None)
        if not self.services[name]:
            del self.services[name]
        try:
            self.on_service_removed(name, addrinfo)
        except Exception:
            self.logger.traceback()
    
    def cmd_query(self, host, name):
        name = name.upper()
        self.logger.debug("querying for %r", name)
        if name not in self.services:
            self.logger.debug("no such service")
            return ()
        
        oldest = time.time() - self.keepalive_timeout
        all_servers = sorted(self.services[name].items(), key = lambda x: x[1])
        servers = []
        for addrinfo, t in all_servers:
            if t < oldest:
                self.logger.debug("discarding stale %s:%s", *addrinfo)
                self.remove_service(name, addrinfo)
            else:
                servers.append(addrinfo)
        
        self.logger.debug("replying with %r", servers)
        return tuple(servers)
    
    def cmd_register(self, host, names, port):
        self.logger.debug("registering %s:%s as %s", host, port, ", ".join(names))
        for name in names:
            self.add_service(name.upper(), (host, port))
        return "OK"
    
    def cmd_unregister(self, host, port):
        self.logger.debug("unregistering %s:%s", host, port)
        for name in self.services.keys():
            self.remove_service(name, (host, port))
        return "OK"
    
    def _work(self):
        while self.active:
            try:
                data, addrinfo = self.sock.recvfrom(MAX_DGRAM_SIZE)
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
            self.sock.sendto(brine.dump(reply), addrinfo)
    
    def start(self):
        if self.active:
            raise ValueError("server is already running")
        if self.sock is None:
            raise ValueError("object disposed")
        self.logger.debug("server started on %s:%s", *self.sock.getsockname())
        try:
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
    
    def stop(self):
        if not self.active:
            raise ValueError("server is not running")
        self.logger.debug("stopping server...")
        self.active = False


def discover_service(name, ip = None, port = None, bcast = None, timeout = 2):
    if ip is None:
        ip = "255.255.255.255"
    if port is None:
        port = REGISTRY_UDP_PORT
    if bcast is None:
        bcast = "255" in ip.split(".")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if bcast:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    data = brine.dump(("RPYC", "QUERY", (name,)))
    sock.sendto(data, (ip, port))
    
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



