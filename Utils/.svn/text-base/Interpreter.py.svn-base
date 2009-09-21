"""
remote interpreter functions
"""
import sys
from Helpers import RedirectedStd


__all__ = ["remote_interpreter", "remote_pm"]

def remote_interpreter(conn, namespace = None):
    """starts an interactive interpreter on the server"""
    if namespace is None:
        namespace = {"conn" : conn}

    std = RedirectedStd(conn)
    try:
        std.redirect()
        conn.modules[__name__]._remote_interpreter_server_side(**namespace)
    finally:
        std.restore()

def _remote_interpreter_server_side(**namespace):
    import code
    namespace.update(globals())
    code.interact(local = namespace)

def remote_pm(conn):
    """a version of pdb.pm() that operates on exceptions at the remote side of the connection"""
    import pdb
    pdb.post_mortem(conn.modules.sys.last_traceback)









