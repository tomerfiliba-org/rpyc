import itertools
import socket
from struct import Struct #@UnusedImport

import consts, brine, netref


import select as select_module
# jython
if hasattr(select_module, 'cpython_compatible_select'):
    from select import cpython_compatible_select as select
else:
    from select import select

class poll(object):
    def __init__(self):
        self._poll = select_module.poll()
    def register(self, fd, mode):
        flags = 0
        if "r" in mode:
            flags |= select_module.POLLIN | select_module.POLLPRI
        if "w" in mode:
            flags |= select_module.POLLOUT
        if "e" in mode:
            flags |= select_module.POLLERR
        if "h" in mode:
            # POLLRDHUP is a linux only extension, not known to python, but nevertheless
            # used and thus needed in the flags
            POLLRDHUP = 0x2000
            flags |= select_module.POLLHUP | select_module.POLLNVAL | POLLRDHUP
        self._poll.register(fd, flags)
    modify = register
    def unregister(self, fd):
        self._poll.unregister(fd)
    def poll(self, timeout = None):
        if timeout:
            # the real poll takes milliseconds while we have seconds here
            timeout = 1000*timeout
        events = self._poll.poll(timeout)
        processed = []
        for fd, evt in events:
            mask = ""
            if evt & (select_module.POLLIN | select_module.POLLPRI):
                mask += "r"
            if evt & select_module.POLLOUT:
                mask += "w"
            if evt & select_module.POLLERR:
                mask += "e"
            if evt & select_module.POLLHUP:
                mask += "h"
            if evt & select_module.POLLNVAL:
                mask += "n"
            processed.append((fd, mask))
        return processed



class Channel(object):
    """Channel implementation.

    Note: In order to avoid problems with all sorts of line-buffered transports,
    we deliberately add ``\\n`` at the end of each frame.
    """

    FRAME_HEADER = Struct("!LB")
    FLUSHER = b"\n" # cause any line-buffered layers below us to flush
    __slots__ = ["stream"]

    def __init__(self, stream):
        self.stream = stream
    def poll(self, timeout):
        """polls the underlying steam for data, waiting up to *timeout* seconds"""
        return self.stream.poll(timeout)
    def recv(self):
        """Receives the next packet (or *frame*) from the underlying stream.
        This method will block until the packet has been read completely

        :returns: string of data
        """
        header = self.stream.read(self.FRAME_HEADER.size)
        length, _ = self.FRAME_HEADER.unpack(header)
        data = self.stream.read(length + len(self.FLUSHER))[:-len(self.FLUSHER)]
        return data
    def send(self, data):
        """Sends the given string of data as a packet over the underlying
        stream. Blocks until the packet has been sent.

        :param data: the byte string to send as a packet
        """
        header = self.FRAME_HEADER.pack(len(data), 0)
        buf = header + data + self.FLUSHER
        self.stream.write(buf)



class Connection(object):

    def __init__(self, service, channel, config = {}, _lazy = False):
        self._channel = channel
        self._seqcounter = itertools.count()
        self._sync_replies = {}
        self._local_objects = {}
        self._proxy_cache = {}
        self._netref_classes_cache = {}
        self._remote_root = None
        self._local_root = service(self)

    def _get_seq_id(self):
        return next(self._seqcounter)

    def _send(self, msg, seq, args):
        self._channel.send(brine.dump((msg, seq, args)))

    def _send_request(self, seq, handler, args):
        self._send(consts.MSG_REQUEST, seq, (handler, self._box(args)))

    def _send_reply(self, seq, obj):
        self._send(consts.MSG_REPLY, seq, self._box(obj))

    def _box(self, obj):
        """store a local object in such a way that it could be recreated on
        the remote party either by-value or by-reference"""
        if brine.dumpable(obj):
            return consts.LABEL_VALUE, obj
        if type(obj) is tuple:
            return consts.LABEL_TUPLE, tuple(self._box(item) for item in obj)
        elif isinstance(obj, netref.BaseNetref) and obj.____conn__ is self:
            return consts.LABEL_LOCAL_REF, obj.____oid__
        else:
            self._local_objects[id(obj)] = obj
            cls = obj.__class__
            if not isinstance(cls, type):
                cls = type(obj)
            return consts.LABEL_REMOTE_REF, (id(obj), cls.__name__, cls.__module__)

    def _unbox(self, package):
        """recreate a local object representation of the remote object: if the
        object is passed by value, just return it; if the object is passed by
        reference, create a netref to it"""
        label, value = package
        if label == consts.LABEL_VALUE:
            return value
        if label == consts.LABEL_TUPLE:
            return tuple(self._unbox(item) for item in value)
        if label == consts.LABEL_LOCAL_REF:
            return self._local_objects[value]
        if label == consts.LABEL_REMOTE_REF:
            oid, clsname, modname = value
            if oid in self._proxy_cache:
                proxy = self._proxy_cache[oid]
                proxy.____refcount__ += 1  # other side increased refcount on boxing,
                                           # if I'm returning from cache instead of new object,
                                           # must increase refcount to match
                return proxy
            proxy = self._netref_factory(oid, clsname, modname)
            self._proxy_cache[oid] = proxy
            return proxy
        raise ValueError("invalid label %r" % (label,))

    #
    # dispatching
    #
    def _dispatch_request(self, seq, raw_args):
        handler, args = raw_args
        args = self._unbox(args)
        res = self._HANDLERS[handler](self, *args)
        self._send_reply(seq, res)

    def _dispatch_reply(self, seq, raw):
        obj = self._unbox(raw)
        self._sync_replies[seq] = obj

    #
    # serving
    #
    def _recv(self, timeout, wait_for_lock):
        if self._channel.poll(timeout):
            data = self._channel.recv()
        else:
            data = None
        return data

    def _dispatch(self, data):
        msg, seq, args = brine.load(data)
        if msg == consts.MSG_REQUEST:
            self._dispatch_request(seq, args)
        elif msg == consts.MSG_REPLY:
            self._dispatch_reply(seq, args)
        else:
            raise ValueError("invalid message type: %r" % (msg,))

    def serve(self, timeout=1, wait_for_lock=True):
        data = self._recv(timeout, wait_for_lock = False)
        if not data:
            return False
        self._dispatch(data)
        return True

    def _netref_factory(self, oid, clsname, modname):
        typeinfo = (clsname, modname)
        if typeinfo in self._netref_classes_cache:
            cls = self._netref_classes_cache[typeinfo]
        elif typeinfo in netref.builtin_classes_cache:
            cls = netref.builtin_classes_cache[typeinfo]
        else:
            info = self.sync_request(consts.HANDLE_INSPECT, oid)
            cls = netref.class_factory(clsname, modname, info)
            self._netref_classes_cache[typeinfo] = cls
        return cls(self, oid)

    # requests
    def sync_request(self, handler, *args):
        seq = self._get_seq_id()
        self._send_request(seq, handler, args)

        while seq not in self._sync_replies:
            self.serve(30)

        return self._sync_replies.pop(seq)

    @property
    def root(self):
        """Fetches the root object (service) of the other party"""
        if self._remote_root is None:
            self._remote_root = self.sync_request(consts.HANDLE_GETROOT)
        return self._remote_root

    def _handle_getroot(self):
        return self._local_root
    def _handle_call(self, oid, args, kwargs=()):
        return self._local_objects[oid](*args, **dict(kwargs))
    def _handle_dir(self, oid):
        return tuple(dir(self._local_objects[oid]))
    def _handle_inspect(self, oid):
        return tuple(netref.inspect_methods(self._local_objects[oid]))

    def _handle_getattr(self, oid, name):
        obj = self._local_objects[oid]
        return getattr(obj, 'exposed_' + str(name))
    def _handle_callattr(self, oid, name, args, kwargs):
        return self._handle_getattr(oid, name)(*args, **dict(kwargs))

    # collect handlers
    _HANDLERS = {}
    for name, obj in dict(locals()).items():
        if name.startswith("_handle_"):
            name2 = "HANDLE_" + name[8:].upper()
            if hasattr(consts, name2):
                _HANDLERS[getattr(consts, name2)] = obj
            else:
                raise NameError("no constant defined for %r", name)
    del name, name2, obj


class SocketStream(object):
    """A stream over a socket"""

    __slots__ = ("sock",)
    MAX_IO_CHUNK = 8000
    def __init__(self, sock):
        self.sock = sock

    @classmethod
    def connect(cls, host, port, family = socket.AF_INET, socktype = socket.SOCK_STREAM,
            proto = 0, timeout = 3):
        family, socktype, proto, _, sockaddr = socket.getaddrinfo(host, port, family,
            socktype, proto)[0]
        s = socket.socket(family, socktype, proto)
        s.settimeout(timeout)
        s.connect(sockaddr)
        return cls(s)

    def poll(self, timeout):
        """indicates whether the stream has data to read (within *timeout*
        seconds)"""
        p = poll()   # from lib.compat, it may be a select object on non-Unix platforms
        p.register(self.sock.fileno(), "r")
        rl = p.poll(timeout)
        return bool(rl)

    def read(self, count):
        data = []
        while count > 0:
            buf = self.sock.recv(min(self.MAX_IO_CHUNK, count))
            data.append(buf)
            count -= len(buf)
        return b"".join(data)

    def write(self, data):
        while data:
            count = self.sock.send(data[:self.MAX_IO_CHUNK])
            data = data[count:]


class Service(object):
    __slots__ = ["_conn", '_counter']

    def __init__(self, conn):
        self._conn = conn
        self._counter = itertools.count(1)

    def on_connect(self): pass
    def on_disconnect(self): pass

    def exposed_ping_test(self):
        count = next(self._counter)
        print("ping: {}".format(count))
        return count
