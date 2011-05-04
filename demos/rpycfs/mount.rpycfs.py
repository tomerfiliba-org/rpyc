# requires fuse bindings for python
import fuse


class RPyCFS(fuse.Fuse):
    def __init__(self, conn, mountpoint):
        self.conn = conn
        fuse.Fuse.__init__(self, mountpoint)

