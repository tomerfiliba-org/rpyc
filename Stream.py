import select
import socket


class Stream(object):
    """
    a stream is a file-like object that is used to expose a consistent and uniform 
    interface to the underlying 'physical' file-like object (like sockets and pipes),
    which have many quirks (sockets may recv() less than `count`, pipes are simplex
    and don't flush, etc.). a stream is always in blocking mode.
    """
    __slots__ = []
    def close(self):
        raise NotImplementedError()
    def fileno(self):
        raise NotImplementedError()
    def is_available(self):
        rlist, wlist, xlist = select.select([self], [], [], 0)
        return bool(rlist)
    def read(self, count):
        raise NotImplementedError()
    def write(self, data):
        raise NotImplementedError()

class SocketStream(Stream):
    """
    a stream that operates over a socket. the socket is expected to be in 
    blocking mode and reliable (i.e., TCP)
    """
    CONNECT_TIMEOUT = 5
    __slots__ = ["sock"]
    def __init__(self, sock):
        self.sock = sock
    def __repr__(self):
        host, port = self.sock.getpeername()
        return "<%s(%s:%d)>" % (self.__class__.__name__, host, port)
    def fileno(self):
        return self.sock.fileno()
    def close(self):
        self.sock.close()
    def read(self, count):
        data = []
        while count > 0:
            buf = self.sock.recv(count)
            if not buf:
                raise EOFError()
            count -= len(buf)
            data.append(buf)
        return "".join(data)
    def write(self, data):
        while data:
            count = self.sock.send(data)
            data = data[count:]
    @classmethod
    def from_new_socket(cls, host, port):
        sock = socket.socket()
        sock.settimeout(cls.CONNECT_TIMEOUT)
        sock.connect((host, port))
        sock.settimeout(None)
        return cls(sock)
    @classmethod
    def from_new_secure_socket(cls, host, port, username, password):
        from tlslite.api import TLSConnection
        stream = cls.from_new_socket(host, port)
        stream.sock = TLSConnection(stream.sock)
        stream.sock.handshakeClientSRP(username, password)
        return stream
    @classmethod
    def from_secure_server_socket(cls, sock, vdb):
        from tlslite.api import TLSConnection
        sock = TLSConnection(sock)
        sock.handshakeServer(verifierDB=vdb)
        return cls(sock)

class PipeStream(Stream):
    """
    a stream that operates over two simplex pipes. the pipes are expected 
    to be in blocking mode
    """
    __slots__ = ["incoming", "outgoing"]
    def __init__(self, incoming, outgoing):
        self.incoming = incoming
        self.outgoing = outgoing
    def fileno(self):
        return self.incoming.fileno()
    def close(self):
        self.incoming.close()
        self.outgoing.close()
    def read(self, count):
        data = []
        while count > 0:
            buf = self.incoming.read(count)
            if not buf:
                raise EOFError()
            count -= len(buf)
            data.append(buf)
        return "".join(data)
    def write(self, data):
        self.outgoing.write(data)
        self.outgoing.flush()

    #
    # win32 stub (can't select() on pipes) -- this stub causes problems with
    # Async objects: doing obj.is_ready blocks. but it's better to have at 
    # least some functionality with pipes on win32 than none at all.
    #
    from sys import platform
    
    if platform == "win32":
        def is_available(self):
            return True


