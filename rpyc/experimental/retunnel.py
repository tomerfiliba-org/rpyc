import socket
import random
import time
from Queue import Queue, Empty as QueueEmpty
from rpyc.core.stream import Stream, TunneledSocketStream, ClosedFile


COOKIE_LENGTH = 8

class ReconnectingTunnelStream(Stream):
    RETRIES = 5

    def __init__(self, remote_machine, destination_port, retries = RETRIES):
        self.remote_machine = remote_machine
        self.destination_port = destination_port
        self.retries = retries
        self.cookie = "".join(chr(random.randint(0, 255)) for _ in range(COOKIE_LENGTH))
        self.stream = None

    def close(self):
        if self.stream is not None and not self.closed:
            self.stream.close()
        self.stream = ClosedFile

    @property
    def closed(self):
        return self.stream is ClosedFile

    def fileno(self):
        return self._safeio(lambda stream: stream.fileno())

    def _reconnect(self):
        # choose random local_port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("localhost", 0))
        local_port = s.getsockname()[1]
        s.close()
        # create a tunnel from local_port:destination_port and connect it
        tun = self.remote_machine.tunnel(local_port, self.destination_port)
        stream = TunneledSocketStream.connect("localhost", local_port)
        stream.write(self.cookie)
        stream.tun = tun
        # print "ReconnectingTunnelStream._reconnect: established a tunnel from localhost:%r to %s:%r" % (
        #    local_port, self.remote_machine, self.destination_port)
        return stream

    def _safeio(self, callback):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        for i in range(self.retries):
            try:
                if not self.stream:
                    self.stream = self._reconnect()
                return callback(self.stream)
            except (EOFError, IOError, OSError, socket.error):
                if i >= self.retries - 1:
                    raise
                if self.stream:
                    self.stream.close()
                self.stream = None
                time.sleep(0.5)

    def write(self, data):
        # print "ReconnectingTunnelStream.write(%r)" % (len(data),)
        return self._safeio(lambda stream: stream.write(data))

    def read(self, count):
        # print "ReconnectingTunnelStream.read(%r)" % (count,)
        return self._safeio(lambda stream: stream.read(count))


class MultiplexingListener(object):
    REACCEPT_TIMEOUT = 10
    RETRIES = 5

    def __init__(self, reaccept_timeout = REACCEPT_TIMEOUT, retries = RETRIES):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reaccept_timeout = reaccept_timeout
        self.retries = retries
        self.client_map = {}

    def close(self):
        self.listener.close()
        self.listener = ClosedFile
    def fileno(self):
        return self.listener.getfileno()
    def getsockname(self):
        return self.listener.getsockname()
    def listen(self, backlog):
        self.listener.listen(backlog)
    def bind(self, addrinfo):
        self.listener.bind(addrinfo)
    def settimeout(self, timeout):
        self.listener.settimeout(timeout)
    def setsockopt(self, level, option, value):
        return self.listener.setsockopt(level, option, value)
    def shutdown(self, mode):
        self.listener.shutdown(mode)

    def accept(self):
        while True:
            # print "MultiplexingListener.accept"
            sock, addrinfo = self.listener.accept()
            cookie = sock.recv(COOKIE_LENGTH)
            # print "MultiplexingListener.accept: got cookie %r" % (cookie,)

            if cookie not in self.client_map:
                self.client_map[cookie] = Queue(1)
                self.client_map[cookie].put(sock)
                # print "MultiplexingListener.accept: new, map=%r" % (self.client_map,)

                resock = ReconnectingSocket(self, cookie, self.retries)
                return resock, addrinfo
            else:
                self.client_map[cookie].put(sock)
                # print "MultiplexingListener.accept: old, map=%r" % (self.client_map,)

    def reaccept(self, cookie):
        # print "MultiplexingListener.reaccept: %r" % (cookie,)
        try:
            return self.client_map[cookie].get(self.reaccept_timeout)
        except QueueEmpty:
            raise EOFError("Client did not reconnect within the timeout")


class ReconnectingSocket(object):
    def __init__(self, listener, cookie, retries):
        self.listener = listener
        self.cookie = cookie
        self.sock = None
        self.retries = retries
        self.blocking_mode = None
    
    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = ClosedFile

    def fileno(self):
        return self._safeio(lambda sock: sock.fileno())
    def getsockname(self):
        return self._safeio(lambda sock: sock.getsockname())
    def getpeername(self):
        return self._safeio(lambda sock: sock.getpeername())
    def shutdown(self, mode):
        if self.sock:
            self.sock.shutdown(mode)

    def setblocking(self, mode):
        self.blocking_mode = mode
        if self.sock:
            self.sock.setblocking(mode)

    def _safeio(self, callback):
        for i in range(self.retries):
            if self.sock is None:
                self.sock = self.listener.reaccept(self.cookie)
                if self.blocking_mode is not None:
                    self.sock.setblocking(self.blocking_mode)

            try:
                return callback(self.sock)
            except (EOFError, IOError, OSError, socket.error):
                if i >= self.retries - 1:
                    raise
                if self.sock:
                    self.sock.close()
                self.sock = None

    def recv(self, count):
        # print "ReconnectingSocket.recv(%r)" % (count,)
        return self._safeio(lambda sock: sock.recv(count))

    def send(self, data):
        # print "ReconnectingSocket.send(%r)" % (len(data),)
        return self._safeio(lambda sock: sock.send(data))









