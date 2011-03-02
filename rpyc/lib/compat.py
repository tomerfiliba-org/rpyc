"""
various library utilities (also for compatibility with python2.4)
"""
try:
    from struct import Struct
except ImportError:
    import struct
    class Struct(object):
        __slots__ = ["format", "size"]
        def __init__(self, format):
            self.format = format
            self.size = struct.calcsize(format)
        def pack(self, *args):
            return struct.pack(self.format, *args)
        def unpack(self, data):
            return struct.unpack(self.format, data)

try:
    all = all
except NameError:
    def all(seq):
        for elem in seq:
            if not elem:
                return False
        return True

try:
    callable = callable
except NameError:
    def callable(obj):
        return hasattr(obj, "__call__")




