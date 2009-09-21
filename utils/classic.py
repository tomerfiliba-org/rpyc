import sys
import os
import inspect
import pdb
import cPickle as pickle
import rpyc
from rpyc import SlaveService
from rpyc.utils import factory


SERVER_FILE = os.path.join(os.path.dirname(rpyc.__file__), "servers", "classic_server.py")
DEFAULT_SERVER_PORT = 18812


#===============================================================================
# connecting
#===============================================================================
def connect_channel(channel):
    return factory.connect_channel(channel, SlaveService)

def connect_stream(stream):
    return factory.connect_stream(stream, SlaveService)

def connect_stdpipes():
    return factory.connect_stdpipes(SlaveService)

def connect_pipes(input, output):
    return factory.connect_pipes(input, output, SlaveService)

def connect(host, port = DEFAULT_SERVER_PORT):
    """creates a socket connection to the given host and port"""
    return factory.connect(host, port, SlaveService)

def tls_connect(host, username, password, port = DEFAULT_SERVER_PORT):
    """creates a secure (TLS) socket connection to the given host and port,
    authenticating with the given username and password"""
    return factory.tls_connect(host, port, username, password, SlaveService)

def connect_subproc():
    """runs an rpyc classic server as a subprocess and return an rpyc
    connection to it"""
    return factory.connect_subproc(["python", "-u", SERVER_FILE, "-q", "-m", "stdio"], 
        SlaveService)

def connect_thread():
    """starts a SlaveService on a thread and connects to it"""
    return factory.connect_thread(SlaveService, remote_service = SlaveService)


#===============================================================================
# remoting utilities
#===============================================================================
def upload(conn, localpath, remotepath, filter = None, ignore_invalid = False):
    """uploads a file or a directory to the given remote path
    localpath - the local file or directory
    remotepath - the remote path
    filter - a predicate that accepts the filename and determines whether 
    it should be uploaded; None means any file"""
    if os.path.isdir(localpath):
        upload_dir(conn, localpath, remotepath, filter)
    elif os.path.isfile(localpath):
        upload_file(conn, localpath, remotepath)
    else:
        if not ignore_invalid:
            raise ValueError("cannot upload %r" % (localpath,))

def upload_file(conn, localpath, remotepath):
    lf = open(localpath, "rb")
    rf = conn.modules.__builtin__.open(remotepath, "wb")
    while True:
        buf = lf.read(16000)
        if not buf:
            break
        rf.write(buf)
    lf.close()
    rf.close()

def upload_dir(conn, localpath, remotepath, filter = None):
    if not conn.modules.os.path.isdir(remotepath):
        conn.modules.os.makedirs(remotepath)
    for fn in os.listdir(localpath):
        if not filter or filter(fn):
            lfn = os.path.join(localpath, fn)
            rfn = conn.modules.os.path.join(remotepath, fn)
            upload(conn, lfn, rfn, filter = filter, ignore_invalid = True)

def download(conn, remotepath, localpath, filter = None, ignore_invalid = False):
    """download a file or a directory to the given remote path
    localpath - the local file or directory
    remotepath - the remote path
    filter - a predicate that accepts the filename and determines whether 
    it should be downloaded; None means any file"""
    if conn.modules.os.path.isdir(remotepath):
        download_dir(conn, remotepath, localpath, filter)
    elif conn.modules.os.path.isfile(remotepath):
        download_file(conn, remotepath, localpath)
    else:
        if not ignore_invalid:
            raise ValueError("cannot download %r" % (remotepath,))

def download_file(conn, remotepath, localpath):
    rf = conn.modules.__builtin__.open(remotepath, "rb")
    lf = open(localpath, "wb")
    while True:
        buf = rf.read(16000)
        if not buf:
            break
        lf.write(buf)
    lf.close()
    rf.close()

def download_dir(conn, remotepath, localpath, filter = None):
    if not os.path.isdir(localpath):
        os.makedirs(localpath)
    for fn in conn.modules.os.listdir(remotepath):
        if not filter or filter(fn):
            rfn = conn.modules.os.path.join(remotepath, fn)
            lfn = os.path.join(localpath, fn)
            download(conn, rfn, lfn, filter = filter, ignore_invalid = True)

def upload_package(conn, module, remotepath = None):
    """uploads a module or a package to the remote party"""
    if remotepath is None:
        site = conn.modules["distutils.sysconfig"].get_python_lib()
        remotepath = conn.modules.os.path.join(site, module.__name__)
    localpath = os.path.dirname(inspect.getsourcefile(module))
    upload(conn, localpath, remotepath)

upload_module = upload_package

def update_module(conn, module):
    """replaces a module on the remote party"""
    rmodule = conn.modules[module.__name__]
    lf = inspect.getsourcefile(module)
    rf = conn.modules.inspect.getsourcefile(rmodule)
    upload_file(conn, lf, rf)
    c.modules.__builtin__.reload(rmodule)

def obtain(proxy):
    """obtains (recreates) a remote object proxy from the other party. 
    the object is moved by *value*, so changes made to it will not reflect 
    on the remote object"""
    return pickle.loads(pickle.dumps(proxy))

def deliver(conn, localobj):
    """delivers (recreates) a local object on the other party. the object is
    moved by *value*, so changes made to it will not reflect on the local 
    object. returns a proxy to the remote object"""
    return conn.modules.cPickle.loads(pickle.dumps(localobj))

class redirected_stdio(object):
    """redirects the other party's stdin, stdout and stderr to those of the 
    local party, so remote STDIO will occur locally"""
    def __init__(self, conn):
        self._restored = True
        self.conn = conn
        self.orig_stdin = self.conn.modules.sys.stdin
        self.orig_stdout = self.conn.modules.sys.stdout
        self.orig_stderr = self.conn.modules.sys.stderr
        self.conn.modules.sys.stdin = sys.stdin
        self.conn.modules.sys.stdout = sys.stdout
        self.conn.modules.sys.stderr = sys.stderr
        self._restored = False
    def __del__(self):
        self.restore()
    def restore(self):
        if self._restored:
            return
        self._restored = True
        self.conn.modules.sys.stdin = self.orig_stdin
        self.conn.modules.sys.stdout = self.orig_stdout
        self.conn.modules.sys.stderr = self.orig_stderr
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.restore()

#== compatibility with python 2.4 ==
#@contextmanager
#def redirected_stdio(conn):
#    orig_stdin = conn.modules.sys.stdin
#    orig_stdout = conn.modules.sys.stdout
#    orig_stderr = conn.modules.sys.stderr
#    try:
#        conn.modules.sys.stdin = sys.stdin
#        conn.modules.sys.stdout = sys.stdout
#        conn.modules.sys.stderr = sys.stderr
#        yield
#    finally:
#        conn.modules.sys.stdin = orig_stdin
#        conn.modules.sys.stdout = orig_stdout
#        conn.modules.sys.stderr = orig_stderr

def pm(conn):
    """pdb.pm on a remote exception"""
    #pdb.post_mortem(conn.root.getconn()._last_traceback)
    redir = redirected_stdio(conn)
    try:
        conn.modules.pdb.post_mortem(conn.root.getconn()._last_traceback)
    finally:
        redir.restore()

def interact(conn, namespace = None):
    """remote interactive interpreter"""
    if namespace is None:
        namespace = {}
    namespace["conn"] = conn
    redir = redirected_stdio(conn)
    try:
        conn.execute("""def _rinteract(ns):
            import code
            code.interact(local = dict(ns))""")
        conn.namespace["_rinteract"](namespace)
    finally:
        redir.restore()




