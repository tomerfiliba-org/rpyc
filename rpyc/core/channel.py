"""*Channel* is an abstraction layer over streams that works with *packets of data*,
rather than an endless stream of bytes, and adds support for compression.
"""
from rpyc.lib import safe_import
from rpyc.lib.compat import Struct, BYTES_LITERAL
zlib = safe_import("zlib")

# * 64 bit length field?
# * separate \n into a FlushingChannel subclass?
# * add thread safety as a subclass?


class Channel(object):
    """Channel implementation.

    Note: In order to avoid problems with all sorts of line-buffered transports,
    we deliberately add ``\\n`` at the end of each frame.
    """

    COMPRESSION_THRESHOLD = 3000
    COMPRESSION_LEVEL = 1
    FRAME_HEADER = Struct("!LB")
    FLUSHER = BYTES_LITERAL("\n")  # cause any line-buffered layers below us to flush
    __slots__ = ["stream", "compress"]

    def __init__(self, stream, compress=True):
        self.stream = stream
        if not zlib:
            compress = False
        self.compress = compress

    def close(self):
        """closes the channel and underlying stream"""
        self.stream.close()

    @property
    def closed(self):
        """indicates whether the underlying stream has been closed"""
        return self.stream.closed

    def fileno(self):
        """returns the file descriptor of the underlying stream"""
        return self.stream.fileno()

    def poll(self, timeout):
        """polls the underlying steam for data, waiting up to *timeout* seconds"""
        return self.stream.poll(timeout)

    def recv(self):
        """Receives the next packet (or *frame*) from the underlying stream.
        This method will block until the packet has been read completely

        :returns: string of data
        """
        header = self.stream.read(self.FRAME_HEADER.size)
        length, compressed = self.FRAME_HEADER.unpack(header)
        data = self.stream.read(length + len(self.FLUSHER))[:-len(self.FLUSHER)]
        if compressed:
            data = zlib.decompress(data)
        return data

    def send(self, data):
        """Sends the given string of data as a packet over the underlying
        stream. Blocks until the packet has been sent.

        :param data: the byte string to send as a packet
        """
        if self.compress and len(data) > self.COMPRESSION_THRESHOLD:
            compressed = 1
            data = zlib.compress(data, self.COMPRESSION_LEVEL)
        else:
            compressed = 0
        data_size = len(data)
        header = self.FRAME_HEADER.pack(data_size, compressed)
        flush_size = len(self.FLUSHER)
        if self.FRAME_HEADER.size + data_size + flush_size <= self.stream.MAX_IO_CHUNK:
            # avoid overhead from socket writes requiring GIL to be held
            self.stream.write(header + data + self.FLUSHER)
        else:
            # Data larger than 64KB, the extra writes are negligible
            part1 = self.stream.MAX_IO_CHUNK - self.FRAME_HEADER.size
            self.stream.write(header + data[:part1])
            self.stream.write(data[part1:])
            self.stream.write(self.FLUSHER)
