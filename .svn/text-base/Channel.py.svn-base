from threading import RLock
import struct


class Channel(object):
    """
    a channel transfers frames over a stream. a frame is any blob of data,
    up to 4GB in size. it is made of a type field (byte), a sequence number
    (dword), and a length field (dword), followed by raw data. at the end
    of the frame, a new line marker (\\r\\n) is appended, to make sure the
    transport layer will send the message without buffering (to overcome 
    newline buffering). apart from that, channels are duplex, and can do both
    sending and receiving in a thread-safe manner.
    """
    HEADER_FORMAT = "<BLL"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    __slots__ = ["send_lock", "recv_lock", "stream", "seq"]

    def __init__(self, stream):
        self.send_lock = RLock()
        self.recv_lock = RLock()
        self.stream = stream
        self.seq = 0
    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self.stream)
    def close(self):
        self.stream.close()
    def fileno(self):
        return self.stream.fileno()
    def is_available(self):
        return self.stream.is_available()
    
    def send(self, type, seq, data):
        """sends the given (type, seq, data) frame"""
        try:
            self.send_lock.acquire()
            if seq is None:
                seq = self.seq
                self.seq += 1
            header = struct.pack(self.HEADER_FORMAT, type, seq, len(data))
            self.stream.write(header + data + "\r\n")
            return seq
        finally:
            self.send_lock.release()

    def recv(self):
        """returns the next (type, seq, data) frame (blocking)"""
        try:
            self.recv_lock.acquire()
            type, seq, length = struct.unpack(self.HEADER_FORMAT, self.stream.read(self.HEADER_SIZE))
            data = self.stream.read(length)
            self.stream.read(2)
            return type, seq, data
        finally:
            self.recv_lock.release()


