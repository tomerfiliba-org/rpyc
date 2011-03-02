"""
rpyc registry server implementation
"""
import sys
import socket
import time
from rpyc.core import brine
from rpyc.utils.logger import Logger


DEFAULT_PRUNING_TIMEOUT = 4 * 60
MAX_DGRAM_SIZE          = 1500
REGISTRY_PORT           = 18811


#------------------------------------------------------------------------------ 
# servers
#------------------------------------------------------------------------------ 

class RegistryServer(object):
    def __init__(self, listenersock, pruning_timeout = None, logger = None):
        self.sock = listenersock
        self.active = False
        self.services = {}
        if pruning_timeout is None:
            pruning_timeout = DEFAULT_PRUNING_TIMEOUT
        self.pruning_timeout = pruning_timeout
        if logger is None:
            logger = Logger("REGSRV")
        self.logger = logger
    
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
        
        oldest = time.time() - self.pruning_timeout
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
                self.logger.warn("invalid magic: %r", magic)
                continue
            cmdfunc = getattr(self, "cmd_%s" % (cmd.lower(),), None)
            if not cmdfunc:
                self.logger.warn("unknown command: %r", cmd)
                continue
            
            try:
                reply = cmdfunc(addrinfo[0], *args)
            except Exception:
                self.logger.traceback()
            else:
                self._send(brine.dump(reply), addrinfo)
    
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
    
    def close(self):
        if not self.active:
            raise ValueError("server is not running")
        self.logger.debug("stopping server...")
        self.active = False

class UDPRegistryServer(RegistryServer):
    def __init__(self, host = "0.0.0.0", port = REGISTRY_PORT, 
    pruning_timeout = None, logger = None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        sock.settimeout(0.5)
        super(UDPRegistryServer, self).__init__(sock, 
            pruning_timeout = pruning_timeout, logger = logger)
    
    def _recv(self):
        return self.sock.recvfrom(MAX_DGRAM_SIZE)
    
    def _send(self, data, addrinfo):
        try:
            self.sock.sendto(data, addrinfo)
        except (socket.error, socket.timeout):
            pass

class TCPRegistryServer(RegistryServer):
    def __init__(self, host = "0.0.0.0", port = REGISTRY_PORT, 
    pruning_timeout = None, logger = None, reuse_addr = True):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reuse_addr and sys.platform != "win32":
            # warning: reuseaddr is not what you expect on windows!
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(10)
        sock.settimeout(0.5)
        super(TCPRegistryServer, self).__init__(sock, 
            pruning_timeout = pruning_timeout, logger = logger)
        self._connected_sockets = {}
    
    def _recv(self):
        sock2 = self.sock.accept()[0]
        addrinfo = sock2.getpeername()
        data = sock2.recv(MAX_DGRAM_SIZE)
        self._connected_sockets[addrinfo] = sock2
        return data, addrinfo
    
    def _send(self, data, addrinfo):
        sock2 = self._connected_sockets.pop(addrinfo)
        try:
            sock2.send(data)
        except (socket.error, socket.timeout):
            pass

#------------------------------------------------------------------------------ 
# clients (registrars)
#------------------------------------------------------------------------------ 
class RegistryClient(object):
    REREGISTER_INTERVAL = 60
    
    def __init__(self, ip, port, timeout, logger = None):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        if logger is None:
            logger = Logger("REGCLNT")
        self.logger = logger

    def discover(self, name):
        raise NotImplementedError    
    
    def register(self, aliases, port):
        raise NotImplementedError    
    
    def unregister(self, port):
        raise NotImplementedError    

class UDPRegistryClient(RegistryClient):
    def __init__(self, ip = "255.255.255.255", port = REGISTRY_PORT, timeout = 2,
    bcast = None, logger = None):
        super(UDPRegistryClient, self).__init__(ip = ip, port = port, 
            timeout = timeout, logger = logger)
        if bcast is None:
            bcast = "255" in ip.split(".")
        self.bcast = bcast
    
    def discover(self, name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.bcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        data = brine.dump(("RPYC", "QUERY", (name,)))
        sock.sendto(data, (self.ip, self.port))
        sock.settimeout(self.timeout)
        
        try:
            try:
                data, addrinfo = sock.recvfrom(MAX_DGRAM_SIZE)
            except (socket.error, socket.timeout):
                servers = ()
            else:
                servers = brine.load(data)
        finally:
            sock.close()
        return servers    
    
    def register(self, aliases, port):
        self.logger.info("registering on %s:%s", self.ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.bcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        data = brine.dump(("RPYC", "REGISTER", (aliases, port)))
        sock.sendto(data, (self.ip, self.port))
        
        tmax = time.time() + self.timeout
        while time.time() < tmax:
            sock.settimeout(tmax - time.time())
            try:
                data, (rip, rport) = sock.recvfrom(MAX_DGRAM_SIZE)
            except socket.timeout:
                self.logger.warn("no registry acknowledged")
                break
            if rport != self.port:
                continue
            try:
                reply = brine.load(data)
            except Exception:
                continue
            if reply == "OK":
                self.logger.info("registry %s:%s acknowledged", rip, rport)
                break
        else:
            self.logger.warn("no registry acknowledged")
        sock.close()
    
    def unregister(self, port):
        self.logger.info("unregistering from %s:%s", self.ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.bcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        data = brine.dump(("RPYC", "UNREGISTER", (port,)))
        sock.sendto(data, (self.ip, self.port))
        sock.close()


class TCPRegistryClient(RegistryClient):
    def __init__(self, ip, port = REGISTRY_PORT, timeout = 2, logger = None):
        super(TCPRegistryClient, self).__init__(ip = ip, port = port, 
            timeout = timeout, logger = logger)
    
    def discover(self, name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        data = brine.dump(("RPYC", "QUERY", (name,)))
        sock.connect((self.ip, self.port))
        sock.send(data)
        
        try:
            try:
                data = sock.recv(MAX_DGRAM_SIZE)
            except (socket.error, socket.timeout):
                servers = ()
            else:
                servers = brine.load(data)
        finally:
            sock.close()
        return servers    
    
    def register(self, aliases, port):
        self.logger.info("registering on %s:%s", self.ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        data = brine.dump(("RPYC", "REGISTER", (aliases, port)))
        
        try:
            try:
                sock.connect((self.ip, self.port))
                sock.send(data)
            except (socket.error, socket.timeout):
                self.logger.warn("could not connect to registry")
                return
            try:
                data = sock.recv(MAX_DGRAM_SIZE)
            except socket.timeout:
                self.logger.warn("registry did not acknowledge")
                return
            try:
                reply = brine.load(data)
            except Exception:
                self.logger.warn("received corrupted data from registry")
                return 
            if reply == "OK":
                self.logger.info("registry %s:%s acknowledged", self.ip, self.port)
        finally:
            sock.close()
    
    def unregister(self, port):
        self.logger.info("unregistering from %s:%s", self.ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        data = brine.dump(("RPYC", "UNREGISTER", (port,)))
        try:
            sock.connect((self.ip, self.port))
            sock.send(data)
        except (socket.error, socket.timeout):
            self.logger.warn("could not connect to registry")
        sock.close()











