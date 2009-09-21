"""
various helper functions
"""
import sys
import cPickle as pickle
from Builtins import isinstance
from Rpyc.Lib import orig_isinstance
from Rpyc.NetProxy import NetProxy, _get_conn
from types import CodeType as code, FunctionType as function


__all__ = ["obtain", "deliver", "isproxy", "getconn", "RedirectedStd", "DeliveringNamespace"]

def isproxy(obj):
    """indicates whether the given object is a NetProxy"""
    return orig_isinstance(obj, NetProxy)

def getconn(obj):
    """returns the connection of a NetProxy"""
    if not isproxy(obj):
        raise TypeError("`obj` is not a NetProxy")
    return _get_conn(obj)

def _dump_function(func):
    """serializes a function"""
    func_info = (
        func.func_name,
        func.func_defaults,
        func.func_closure,        
    )
    code_info = (
        func.func_code.co_argcount,
        func.func_code.co_nlocals,
        func.func_code.co_stacksize,
        func.func_code.co_flags,
        func.func_code.co_code,
        func.func_code.co_consts,
        func.func_code.co_names,
        func.func_code.co_varnames,
        func.func_code.co_filename,
        func.func_code.co_name,
        func.func_code.co_firstlineno,
        func.func_code.co_lnotab,
        func.func_code.co_freevars,
        func.func_code.co_cellvars,
    )
    return pickle.dumps((code_info, func_info, func.func_doc), pickle.HIGHEST_PROTOCOL)

def _load_function(pickled_func, globals):
    """recreates a serialized function"""
    code_info, func_info, doc = pickle.loads(pickled_func)
    func = function(code(*code_info), globals, *func_info)
    func.func_doc = doc
    return func

def obtain(proxy):
    """
    obtains (brings forth) a remote object. the object can be a function or 
    any picklable object. obtaining objects creates a local copy of the remote 
    object, so changes made to the local copy are not reflected on the remote 
    one. keep this in mind.
    
    proxy - any proxy to a remote object
    returns a "real" object
    """
    if not isproxy(proxy):
        raise TypeError("object must be a proxy")
    if isinstance(proxy, function):
        globals = getconn(proxy)._local_namespace
        return _load_function(_dump_function(proxy), globals)
    else:
        return pickle.loads(getconn(proxy).modules.cPickle.dumps(proxy, pickle.HIGHEST_PROTOCOL))

def deliver(obj, conn):
    """
    delivers a local object to the other side of the connection. the object
    can be a function or any picklable object. deliver objects creates a remote
    copy of the objectm so changes made to the remote copy are not reflected on
    the local one. keep this in mind.
    
    obj - the object to deliver
    conn - the connection which obtains the object
    returns a proxy to the delivered object
    """
    if isproxy(obj):
        raise TypeError("can't deliver proxies")
    if orig_isinstance(obj, function):
        globals = conn.remote_conn._local_namespace
        dumped = _dump_function(obj)
        return conn.modules[__name__]._load_function(dumped, globals)
    else:
        return conn.modules.cPickle.loads(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))

class DeliveringNamespace(object):
    """delivering namesapce: getattr`ing from this object returns a proxy,
    while setattr`ing this object delivers the given object to the remote side
    of the connection"""
    __slots__ = ["____conn__"]
    def __init__(self, conn):
        object.__setattr__(self, "____conn__", conn)
    def __getattr__(self, name):
        return _get_conn(self).namespace[name]
    def __setattr__(self, name, value):
        if isproxy(value):
            if _get_conn(value) is not _get_conn(self):
                raise TypeError("proxies must belong to the namespace's connection")
            _get_conn(self).namespace[name] = value
        else:
            _get_conn(self).namespace[name] = deliver(value, _get_conn(self))

class RedirectedStd(object):
    """redirected std[in|out|err] context"""
    __slots__ = ["conn", "redirected", "orig_stdin", "orig_stdout", "orig_strerr"]
    def __init__(self, conn):
        self.conn = conn
        self.redirected = False
    def __del__(self):
        self.restore()
    def redirect(self):
        if self.redirected:
            return
        self.orig_stdin = self.conn.modules.sys.stdin
        self.orig_stdout = self.conn.modules.sys.stdout
        self.orig_strerr = self.conn.modules.sys.stderr
        self.conn.modules.sys.stdin = sys.stdin
        self.conn.modules.sys.stdout = sys.stdout
        self.conn.modules.sys.stderr = sys.stderr
        self.redirected = True
    def restore(self):
        if not self.redirected:
            return
        self.conn.modules.sys.stdin = self.orig_stdin
        self.conn.modules.sys.stdout = self.orig_stdout
        self.conn.modules.sys.stderr = self.orig_strerr
        self.redirected = False














