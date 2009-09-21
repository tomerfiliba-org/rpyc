"""
abstraction layer over OS-depenedent byte streams
"""
import sys
import os
import socket
import time
import errno
from select import select
from rpyc.utils.lib import safe_import
win32file = safe_import("win32file")
win32pipe = safe_import("win32pipe")
msvcrt = safe_import("msvcrt")


retry_errnos = set([errno.EAGAIN])
if hasattr(errno, "WSAEWOULDBLOCK"):
    retry_errnos.add(errno.WSAEWOULDBLOCK)


class Stream(object):
    __slots__ = ()
    def close(self):
        raise NotImplementedError()
    @property
    def closed(self):
        raise NotImplementedError()
    def fileno(self):
        raise NotImplementedError()
    def poll(self, timeout):
        """indicate whether the stream has data to read"""
        rl, wl, xl = select([self], [], [], timeout)
        return bool(rl)
    def read(self, count):
        """read exactly `count` bytes, or raise EOFError"""
        raise NotImplementedError()
    def write(self, data):
        """write the entire `data`, or raise EOFError"""
        raise NotImplementedError()


class ClosedFile(object):
    """represents a closed file object (singleton)"""
    __slots__ = ()
    def __getattr__(self, name):
        raise EOFError("stream has been closed")
    def close(self):
        pass
    @property
    def closed(self):
        return True
    def fileno(self):
        raise EOFError("stream has been closed")
ClosedFile = ClosedFile()


class SocketStream(Stream):
    __slots__ = ("sock",)
    MAX_IO_CHUNK = 8000
    def __init__(self, sock):
        self.sock = sock
    @classmethod
    def _connect(cls, host, port, family = socket.AF_INET, type = socket.SOCK_STREAM, 
    proto = 0, timeout = 3):
        s = socket.socket(family, type, proto)
        s.settimeout(timeout)
        s.connect((host, port))
        return s
    @classmethod
    def connect(cls, host, port, **kwargs):
        return cls(cls._connect(host, port, **kwargs))
    @classmethod
    def tls_connect(cls, host, port, username, password, **kwargs):
        from tlslite.api import TLSConnection
        s = cls._connect(host, port, **kwargs)
        s2 = TLSConnection(s)
        s2.fileno = lambda fd=s.fileno(): fd
        s2.handshakeClientSRP(username, password)
        return cls(s2)
    @property
    def closed(self):
        return self.sock is ClosedFile
    def close(self):
        if not self.closed:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
        self.sock.close()
        self.sock = ClosedFile
    def fileno(self):
        return self.sock.fileno()
    def read(self, count):
        data = []
        while count > 0:
            try:
                buf = self.sock.recv(min(self.MAX_IO_CHUNK, count))
            except socket.timeout:
                continue
            except socket.error, ex:
                if ex[0] in retry_errnos:
                    # windows just has to be a bitch
                    continue
                self.close()
                raise EOFError(ex)
            if not buf:
                self.close()
                raise EOFError("connection closed by peer")
            data.append(buf)
            count -= len(buf)
        return "".join(data)
    def write(self, data):
        try:
            while data:
                count = self.sock.send(data[:self.MAX_IO_CHUNK])
                data = data[count:]
        except socket.error, ex:
            self.close()
            raise EOFError(ex)

class PipeStream(Stream):
    __slots__ = ("incoming", "outgoing")
    MAX_IO_CHUNK = 32000
    def __init__(self, incoming, outgoing):
        outgoing.flush()
        self.incoming = incoming
        self.outgoing = outgoing
    @classmethod
    def from_std(cls):
        return cls(sys.stdin, sys.stdout)
    @classmethod
    def create_pair(cls):
        r1, w1 = os.pipe()
        r2, w2 = os.pipe()
        side1 = cls(os.fdopen(r1, "rb"), os.fdopen(w2, "wb"))
        side2 = cls(os.fdopen(r2, "rb"), os.fdopen(w1, "wb"))
        return side1, side2
    @property
    def closed(self):
        return self.incoming is ClosedFile
    def close(self):
        self.incoming.close()
        self.outgoing.close()
        self.incoming = ClosedFile
        self.outgoing = ClosedFile
    def fileno(self):
        return self.incoming.fileno()
    def read(self, count):
        data = []
        try:
            while count > 0:
                buf = os.read(self.incoming.fileno(), min(self.MAX_IO_CHUNK, count))
                if not buf:
                    raise EOFError("connection closed by peer")
                data.append(buf)
                count -= len(buf)
        except EOFError:
            self.close()
            raise
        except EnvironmentError, ex:
            self.close()
            raise EOFError(ex)
        return "".join(data)
    def write(self, data):
        try:
            while data:
                chunk = data[:self.MAX_IO_CHUNK]
                written = os.write(self.outgoing.fileno(), chunk)
                data = data[written:]
        except EnvironmentError, ex:
            self.close()
            raise EOFError(ex)


class Win32PipeStream(Stream):
    """win32 has to suck"""
    __slots__ = ("incoming", "outgoing", "_fileno")
    PIPE_BUFFER_SIZE = 130000
    MAX_IO_CHUNK = 32000
    
    def __init__(self, incoming, outgoing):
        if hasattr(incoming, "fileno"):
            self._fileno = incoming.fileno()
            incoming = msvcrt.get_osfhandle(incoming.fileno())
        if hasattr(outgoing, "fileno"):
            outgoing = msvcrt.get_osfhandle(outgoing.fileno())
        self.incoming = incoming
        self.outgoing = outgoing
    @classmethod
    def from_std(cls):
        return cls(sys.stdin, sys.stdout)
    @classmethod
    def create_pair(cls):
        r1, w1 = win32pipe.CreatePipe(None, cls.PIPE_BUFFER_SIZE)
        r2, w2 = win32pipe.CreatePipe(None, cls.PIPE_BUFFER_SIZE)
        return cls(r1, w2), cls(r2, w1)
    
    def fileno(self):
        return self._fileno
    @property
    def closed(self):
        return self.incoming is ClosedFile
    def close(self):
        if self.closed:
            return
        win32file.CloseHandle(self.incoming)
        win32file.CloseHandle(self.outgoing)
        self.incoming = ClosedFile
        self.outgoing = ClosedFile
    def read(self, count):
        try:
            data = []
            while count > 0:
                dummy, buf = win32file.ReadFile(self.incoming, min(self.MAX_IO_CHUNK, count))
                count -= len(buf)
                data.append(buf)
        except TypeError, ex:
            if not self.closed:
                raise
            raise EOFError(ex)
        except win32file.error, ex:
            self.close()
            raise EOFError(ex)
        return "".join(data)
    def write(self, data):
        try:
            while data:
                dummy, count = win32file.WriteFile(self.outgoing, data[:self.MAX_IO_CHUNK])
                data = data[count:]
        except TypeError, ex:
            if not self.closed:
                raise
            raise EOFError(ex)
        except win32file.error, ex:
            self.close()
            raise EOFError(ex)
    
    def poll(self, timeout, interval = 0.1):
        """a poor man's version of select()"""
        if timeout is None:
            timeout = sys.maxint
        length = 0
        tmax = time.time() + timeout
        try:
            while length == 0:
                length = win32pipe.PeekNamedPipe(self.incoming, 0)[1]
                if time.time() >= tmax:
                    break
                time.sleep(interval)
        except TypeError, ex:
            if not self.closed:
                raise
            raise EOFError(ex)
        return length != 0


class NamedPipeStream(Win32PipeStream):
    NAMED_PIPE_PREFIX = r'\\.\pipe\rpyc_'
    PIPE_IO_TIMEOUT = 3
    CONNECT_TIMEOUT = 3
    __slots__ = ("is_server_side",)
    
    def __init__(self, handle, is_server_side):
        Win32PipeStream.__init__(self, handle, handle)
        self.is_server_side = is_server_side
    @classmethod
    def from_std(cls):
        raise NotImplementedError()
    @classmethod
    def create_pair(cls):    
        raise NotImplementedError()
    
    @classmethod
    def create_server(cls, pipename, connect = True):
        if not pipename.startswith("\\\\."):
            pipename = cls.NAMED_PIPE_PREFIX + pipename
        handle = win32pipe.CreateNamedPipe( 
            pipename, 
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
            1,
            cls.PIPE_BUFFER_SIZE,
            cls.PIPE_BUFFER_SIZE,
            cls.PIPE_IO_TIMEOUT * 1000,
            None
        )
        inst = cls(handle, True)
        if connect:
            inst.connect_server()
        return inst
    
    def connect_server(self):
        if not self.is_server_side:
            raise ValueError("this must be the server side")
        win32pipe.ConnectNamedPipe(self.incoming, None)
    
    @classmethod
    def create_client(cls, pipename, timeout = CONNECT_TIMEOUT):
        if not pipename.startswith("\\\\."):
            pipename = cls.NAMED_PIPE_PREFIX + pipename
        handle = win32file.CreateFile(
            pipename, 
            win32file.GENERIC_READ | win32file.GENERIC_WRITE, 
            0, 
            None,
            win32file.OPEN_EXISTING, 
            0, 
            None
        )
        return cls(handle, False) 
    
    def close(self):
        if self.closed:
            return
        if self.is_server_side:
            win32file.FlushFileBuffers(self.outgoing)
            win32pipe.DisconnectNamedPipe(self.outgoing)
        Win32PipeStream.close(self)


if sys.platform == "win32":    
    PipeStream = Win32PipeStream








