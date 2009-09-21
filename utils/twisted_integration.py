"""
rpyc-twisted integration, based on code originally contributed by noam raphael

Note: rpyc normally works in blocking (synchornous) fashion, for instance,
getting an attribute of an object (foo.bar.baz). the twistedish solution
would be using @inlineCallbacks and `yield (yield foo.bar).baz`... which is
rather less pythonistic.  

function calls, however, can be made asynchronous easily with the async() 
wrapper, so these will play nicely with twisted.

all in all, the integration with twisted is limited and rather fake. 
working with rpyc might block the reactor -- a bad thing -- but a necessary 
evil if we wish to combine the two methodologies.

if you find a better solution, please tell me.
"""
import socket
import rpyc
from rpyc.core import SocketStream, Channel
import twisted.internet.protocol as tip
from twisted.internet import reactor
from twisted.python import log


class TwistedSocketStream(SocketStream):
    def __init__(self, transport):
        SocketStream.__init__(self, transport.socket)
        self.transport = transport
        self._buffer = ""
    def push(self, data):
        self._buffer += data
    
    def poll(self, timeout):
        if self._buffer:
            return True
        self.sock.setblocking(True)
        try:
            return SocketStream.poll(self, timeout)
        finally:
            try:
                self.sock.setblocking(False)
            except socket.error:
                pass
    
    def read(self, count):
        if count <= len(self._buffer):
            data = self._buffer[:count]
            self._buffer = self._buffer[count:]
        else:
            self.sock.setblocking(True)
            try:
                data2 = SocketStream.read(self, count - len(self._buffer))
            finally:
                try:
                    self.sock.setblocking(False)
                except socket.error:
                    pass
            data = self._buffer + data2
            self._buffer = ""
        #log.msg("%s.read(%r)" % (self, data))
        return data
    
    def write(self, data):
        #log.msg("%s.write(%r)" % (self, data))
        self.sock.setblocking(True)
        try:
            SocketStream.write(self, data)
        finally:
            self.sock.setblocking(False)


class TwistedRpycProtocol(tip.Protocol):
    def __init__(self):
        self.stream = None
        self.conn = None
    def connectionMade(self):
        self.stream = TwistedSocketStream(self.transport)
        self.conn = rpyc.Connection(self.factory.service, Channel(self.stream), 
            config = self.factory.config, _lazy = True)
        self.conn._init_service()
        if self.factory.logging:
            log.msg("%s: connected %s" % (self, self.conn))
        if self.factory.on_connected is not None:
            reactor.callLater(0, self.factory.on_connected, self.conn)
    def connectionLost(self, reason=None):
        if self.conn:
            if self.factory.logging:
                log.msg("%s: closing connection %s" % (self, self.conn))
            c = self.conn
            self.conn = None
            c.close(_catchall = True)
    def dataReceived(self, data):
        self.stream.push(data)
        self.conn.poll_all()


class RpycClientFactory(tip.ClientFactory):
    protocol = TwistedRpycProtocol
    def __init__(self, service, on_connected = None, config = {}, logging = False):
        self.service = service
        self.config = config
        self.on_connected = on_connected
        self.logging = logging


RpycServerFactory = RpycClientFactory


