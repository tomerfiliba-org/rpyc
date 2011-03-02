"""
channel - an abstraction layer over streams that works with data frames
(rather than bytes) and supports compression.
Note: in order to avoid problems with all sorts of line-buffered transports,
we deliberately add \\n at the end of each frame.

note: unlike previous versions, this is no longer thread safe
"""
import zlib
from rpyc.utils.lib import Struct

# * 64 bit length field?
# * separate \n into a FlushingChannel subclass?
# * add thread safety as a subclass?

class Channel(object):
    COMPRESSION_THRESHOLD = 3000
    COMPRESSION_LEVEL = 1
    FRAME_HEADER = Struct("!LB")
    FLUSHER = "\n" # cause any line-buffered layers below us to flush
    __slots__ = ["stream", "compress"]
    
    def __init__(self, stream, compress = True):
        self.stream = stream
        self.compress = compress
    def close(self):
        self.stream.close()
    @property
    def closed(self):
        return self.stream.closed
    def fileno(self):
        return self.stream.fileno()
    def poll(self, timeout):
        return self.stream.poll(timeout)
    def recv(self):
        header = self.stream.read(self.FRAME_HEADER.size)
        length, compressed = self.FRAME_HEADER.unpack(header)
        data = self.stream.read(length + len(self.FLUSHER))[:-len(self.FLUSHER)]
        if compressed:
            data = zlib.decompress(data)
        return data
    def send(self, data):
        if self.compress and len(data) > self.COMPRESSION_THRESHOLD:
            compressed = 1
            data = zlib.compress(data, self.COMPRESSION_LEVEL)
        else:
            compressed = 0
        header = self.FRAME_HEADER.pack(len(data), compressed)
        buf = header + data + self.FLUSHER
        self.stream.write(buf)




