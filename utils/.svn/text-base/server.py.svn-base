"""
rpyc plug-in server (threaded or forking)

authenticators: the server instance can also take an authenticator object,
which is basically any callable (i.e., a function) that takes the newly
connected socket and "authenticates" it. this authenticator should return
a socket-like object, or raise AuthenticationError if it fails.

a very trivial authenticator may be
    def magic_word_authenticator(sock):
        if sock.recv(5) != "Ma6ik":
            raise AuthenticationError("wrong magic word")
        return sock

your authenticator can return any socket-like object. for instance, it may 
authenticate the client and return a TLS/SSL-wrapped socket object that 
encrypts the transport.

rpyc includes integration with tlslite, a TLS/SSL library. the VdbAuthenticator
class can authenticate clients based on username-password pairs.
"""
import sys
import os
import socket
import time
import threading
import signal
import select
from rpyc.core.consts import DEFAULT_SERVER_PORT, REGISTRY_UDP_PORT
from rpyc.core import brine, SocketStream, Channel, Connection
from rpyc.utils.logger import Logger
from rpyc.utils.registry import RegistryServer


REGISTRY_IP = "255.255.255.255"
REGISTRY_REPLY_TIMEOUT = 3
REGISTRY_KEEPALIVE_INTERVAL = 60

class AuthenticationError(Exception):
    pass


class VdbAuthenticator(object):
    __slots__ = ["vdb"]
    BITS = 2048
    
    def __init__(self, vdb):
        self.vdb = vdb
    @classmethod
    def from_users(cls, users): 
        from tlslite.api import VerifierDB
        inst = cls(VerifierDB())
        for username, password in users.iteritems():
            inst.set_user(username, password)
        return inst
    @classmethod
    def from_file(cls, filename):
        from tlslite.api import VerifierDB
        vdb = VerifierDB(filename)
        if os.path.exists(filename):
            vdb.open()
        else:
            vdb.create()
        return cls(vdb)
    def set_user(self, username, password):
        self.vdb[username] = self.vdb.makeVerifier(username, password, self.BITS)
    def __call__(self, sock):
        from tlslite.api import TLSConnection
        sock2 = TLSConnection(sock)
        sock2.fileno = lambda fd=sock.fileno(): fd
        try:
            sock2.handshakeServer(verifierDB = self.vdb)
        except Exception, ex:
            raise AuthenticationError(str(ex))
        return sock2


class Server(object):
    def __init__(self, service, hostname = "0.0.0.0", port = 0, backlog = 10, 
    authenticator = None, auto_register = True, protocol_config = {}, 
    reuse_addr = True, registry_ip = REGISTRY_IP, registry_bcast = True,
    registry_port = REGISTRY_UDP_PORT):
        self.service = service
        self.authenticator = authenticator
        self.backlog = backlog
        self.auto_register = auto_register
        self.protocol_config = protocol_config
        self.registry_ip = registry_ip
        self.registry_port = registry_port
        self.registry_bcast = registry_bcast
        self.clients = set()
        self.listener = socket.socket()
        if reuse_addr and sys.platform != "win32":
            # warning: reuseaddr is not what you expect on windows!
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.logger = self._get_logger()
        self.active = False
        self.listener.bind((hostname, port))
        self.port = self.listener.getsockname()[1]
        self._closed = False
    
    def _get_logger(self):
        raise NotImplementedError()
    
    def close(self):
        if self._closed:
            return
        self._closed = True
        self.active = False
        if self.auto_register:
            self.unregister()
        self.listener.close()
        self.logger.info("listener closed")
        for c in set(self.clients):
            try:
                c.shutdown(socket.SHUT_RDWR)
            except:
                pass
            c.close()
        self.clients.clear()
    
    def fileno(self):
        return self.listener.fileno()
    
    def register(self, ip = None, port = None, bcast = None, reply_timeout = REGISTRY_REPLY_TIMEOUT):
        if ip is None:
            ip = self.registry_ip
        if port is None:
            port = self.registry_port
        if bcast is None:
            bcast = self.registry_bcast
        
        self.logger.info("registering on %s:%s", ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        args = (self.service.get_service_aliases(), self.port)
        data = brine.dump(("RPYC", "REGISTER", args))
        sock.sendto(data, (ip, port))
        
        tmax = time.time() + reply_timeout
        while time.time() < tmax:
            sock.settimeout(tmax - time.time())
            try:
                data, (rip, rport) = sock.recvfrom(1000)
            except socket.timeout:
                self.logger.warn("no registry acknowledged")
                break
            if rport != port:
                continue
            try:
                reply = brine.load(data)
            except:
                continue
            if reply == "OK":
                self.logger.info("registry %s:%s acknowledged", rip, rport)
                break
        else:
            self.logger.warn("no registry acknowledged")
        sock.close()
    
    def unregister(self, ip = None, port = None, bcast = None):
        if ip is None:
            ip = self.registry_ip
        if port is None:
            port = self.registry_port
        if bcast is None:
            bcast = self.registry_bcast
        
        self.logger.info("unregistering from %s:%s", ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        data = brine.dump(("RPYC", "UNREGISTER", (self.port,)))
        sock.sendto(data, (ip, port))
        sock.close()
    
    def _bg_register(self):
        self.logger.info("started background auto-register thread, interval = %s", 
            REGISTRY_KEEPALIVE_INTERVAL)
        tnext = 0
        try:
            while self.active:
                t = time.time()
                if t >= tnext: 
                    tnext = t + REGISTRY_KEEPALIVE_INTERVAL
                    self.register()
                time.sleep(1)
        finally:
            if not self._closed:
                self.logger.info("background auto-register thread finished")
    
    def accept(self):
        while True:
            try:
                sock, (h, p) = self.listener.accept()
            except socket.timeout:
                pass
            else:
                break
        sock.setblocking(True)
        self.logger.info("accepted %s:%s", h, p)
        if self.authenticator:
            try:
                sock = self.authenticator(sock)
            except AuthenticationError:
                self.logger.info("%s:%s failed to authenicate, closing socket", h, p)
                sock.close()
                return
            else:
                self.logger.info("%s:%s authenicated successfully", h, p)
        self.clients.add(sock)
        self._accept_method(sock)
    
    def _accept_method(self, sock):
        raise NotImplementedError
    
    def _serve_client(self, sock):
        h, p = sock.getpeername()
        self.logger.info("welcome %s:%s", h, p)
        try:
            conn = Connection(self.service, Channel(SocketStream(sock)), config = self.protocol_config)
            conn.serve_all()
        except select.error:
            if not self._closed:
                raise e
        finally:
            self.logger.info("goodbye %s:%s", h, p)
            self.clients.discard(sock)
    
    def start(self):
        """starts the server. use close() to stop"""
        self.listener.listen(self.backlog)
        h, p = self.listener.getsockname()
        self.logger.info("server started on %s:%s", h, p)
        self.active = True
        if self.auto_register:
            t = threading.Thread(target = self._bg_register)
            t.setDaemon(True)
            t.start()
        if sys.platform == "win32":
            # hack so we can receive Ctrl+C on windows
            self.listener.settimeout(1)
        try:
            try:
                while True:
                    self.accept()
            except KeyboardInterrupt:
                self.logger.warn("user interrupt!")
        finally:
            self.logger.info("server has terminated")
            self.close()


class ThreadedServer(Server):
    def _get_logger(self):
        return Logger(self.service.get_service_name(), show_tid = True)
    
    def _accept_method(self, sock):
        t = threading.Thread(target = self._serve_client, args = (sock,))
        t.setDaemon(True)
        t.start()


class ForkingServer(Server):
    def _get_logger(self):
        return Logger(self.service.get_service_name(), show_pid = True)
    
    def _accept_method(self, sock):
        # we use double-fork to get rid of zombies without having to worry 
        # about EINTR. ugh. forking python processes sucks. 
        pid = os.fork()
        if pid == 0:
            # child
            try:
                self.logger.info("child process created")
                self.listener.close()
                self.unregister = self.register = lambda *a, **k: None
                self.clients.clear()
                if os.fork() == 0:
                    # grandchild
                    try:
                        self.logger.info("grandchild starts serving")
                        self._serve_client(sock)
                    finally:
                        self.logger.info("grandchild terminated")
                        os._exit(0)
            finally:
                self.logger.info("child terminated")
                os._exit(0)
        else:
            # parent
            sock.close()
            os.waitpid(pid, 0)






