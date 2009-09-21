import os
import socket
import sys
import gc
import struct
from threading import Thread
from Rpyc.Connection import Connection
from Rpyc.Stream import SocketStream, PipeStream
from Rpyc.Channel import Channel
from Discovery import UDP_DISCOVERY_PORT, MAX_DGRAM_SIZE, QUERY_MAGIC

DEFAULT_PORT = 18812


#
# utilities
#
class _Logger(object):
    def __init__(self, logfile = None, active = True):
        self.logfile = logfile
        self.active = active
    def __call__(self, *args):
        if self.active and self.logfile:
            text = " ".join(str(a) for a in args)
            self.logfile.write("[%d] %s\n" % (os.getpid(), text))
            self.logfile.flush()

log = _Logger(sys.stdout)

def create_listener_socket(port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
    sock.listen(4)
    log("listening on", sock.getsockname())
    return sock

#
# serving
#
def serve_channel(chan):
    conn = Connection(chan)
    try:
        try:
            while True:
                conn.serve()
        except EOFError:
            pass
    finally:
        conn.close()
        gc.collect()

def serve_socket_helper(sock, secure = False, vdb = None):
    if secure:
        log("requiring authentication")
        try:
            stream = SocketStream.from_secure_server_socket(sock, vdb)
        except:
            log("authenication failed")
            sock.close()
        else:
            log("authentication successful")
            serve_channel(Channel(stream))
    else:
        serve_channel(Channel(SocketStream(sock)))

def serve_socket(sock, **kw):
    sockname = sock.getpeername()
    log("welcome", sockname)
    try:
        try:
            serve_socket_helper(sock, **kw)
        except socket.error:
            pass
    finally:
        log("goodbye", sockname)

def serve_pipes(incoming, outgoing):
    serve_channel(Channel(PipeStream(incoming, outgoing)))

#
# threaded utilities
#
def threaded_server(port = DEFAULT_PORT, **kw):
    sock = create_listener_socket(port)
    while True:
        newsock, name = sock.accept()
        t = Thread(target = serve_socket, args = (newsock,), kwargs = kw)
        t.setDaemon(True)
        t.start()

def start_threaded_server(*args, **kwargs):
    """starts the threaded_server on a separate thread. this turns the 
    threaded_server into a mix-in you can place anywhere in your code"""
    t = Thread(target = threaded_server, args = args, kwargs = kwargs)
    t.setDaemon(True)
    t.start()

#
# discovery
#
def discovery_agent(rpyc_port):
    """
    answers broadcasted queries with the port of the RPyC server on this machine.
    run this agent on a separate thread
    """
    data = struct.pack("<H", rpyc_port)

    # listen
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", UDP_DISCOVERY_PORT))
    log("discovery_agent: started")
    
    # serve
    while True:
        query, addr = s.recvfrom(MAX_DGRAM_SIZE)
        if query == QUERY_MAGIC:
            log("discovery_agent: now answering", addr)
            s.sendto(data, addr)

def start_discovery_agent_thread(*args, **kwargs):
    t = Thread(target = discovery_agent, args = args, kwargs = kwargs)
    t.setDaemon(True)
    t.start()


