import sys
from Boxing import Box, dump_exception, load_exception
from ModuleNetProxy import RootImporter
from Lib import raise_exception, AttrFrontend


FRAME_REQUEST = 1
FRAME_RESULT = 2
FRAME_EXCEPTION = 3

class Connection(object):
    """
    the rpyc connection layer (protocol and APIs). generally speaking, the only 
    things you'll need to access directly from this object are:
     * modules - represents the remote python interprerer's modules namespace
     * execute - executes the given code on the other side of the connection
     * namespace - the namespace in which the code you `execute` resides

    the rest of the attributes should be of no intresent to you, except maybe
    for `remote_conn`, which represents the other side of the connection. it is
    unlikely, however, you'll need to use it (it is used interally).
    
    when you are done using a connection, and wish to release the resources it
    holds, you should call close(). you don't have to, but if you don't, the gc
    can't release the memory because of cyclic references.
    """
    __slots__ = ["_closed", "_local_namespace", "channel", "box", "async_replies",
    "sync_replies", "module_cache", "remote_conn", "modules", "namespace"]
    
    def __init__(self, channel):
        self._closed = False
        self._local_namespace = {}
        self.channel = channel
        self.box = Box(self)
        self.async_replies = {}
        self.sync_replies = {}
        self.module_cache = {}
        self.remote_conn = self.sync_request("handle_getconn")
        # user APIs:
        self.modules = RootImporter(self)
        self.namespace = AttrFrontend(self.remote_conn._local_namespace)
        self.execute("")

    def __repr__(self):
        if self._closed:
            return "<%s.%s(closed)>" % (self.__class__.__module__, self.__class__.__name__)
        else:
            return "<%s.%s(%r)>" % (self.__class__.__module__, self.__class__.__name__, self.channel)

    # 
    # file api layer
    #
    def close(self):
        """closes down the connection and releases all cyclic dependecies"""
        if not self._closed:
            self.box.close()
            self.channel.close()
            self._closed = True
            self._local_namespace = None
            self.channel = None
            self.box = None
            self.async_replies = None
            self.sync_replies = None
            self.module_cache = None
            self.modules = None
            self.remote_conn = None
            self.namespace = None

    def fileno(self):
        """connections are select()able"""
        return self.channel.fileno()

    #
    # protocol
    #
    def send(self, type, seq, obj):
        if self._closed:
            raise EOFError("the connection is closed")
        return self.channel.send(type, seq, self.box.pack(obj))
    
    def send_request(self, handlername, *args):
        return self.send(FRAME_REQUEST, None, (handlername, args))

    def send_exception(self, seq, exc_info):
        self.send(FRAME_EXCEPTION, seq, dump_exception(*exc_info))

    def send_result(self, seq, obj):
        self.send(FRAME_RESULT, seq, obj)

    #
    # dispatching
    #
    def dispatch_result(self, seq, obj):
        if seq in self.async_replies:
            self.async_replies.pop(seq)(obj, False)
        else:        
            self.sync_replies[seq] = obj
    
    def dispatch_exception(self, seq, obj):
        excobj = load_exception(obj)
        if seq in self.async_replies:
            self.async_replies.pop(seq)(excobj, True)
        else:
            raise_exception(*excobj)

    def dispatch_request(self, seq, handlername, args):
        try:
            res = getattr(self, handlername)(*args)
        except SystemExit:
            raise
        except:
            self.send_exception(seq, sys.exc_info())
        else:
            self.send_result(seq, res)

    def poll(self):
        """if available, serves a single request, otherwise returns (non-blocking serve)"""
        if self.channel.is_available():
            self.serve()
            return True
        else:
            return False
    
    def serve(self):
        """serves a single request (may block)"""
        type, seq, data = self.channel.recv()
        if type == FRAME_RESULT:
            self.dispatch_result(seq, self.box.unpack(data))
        elif type == FRAME_REQUEST:
            self.dispatch_request(seq, *self.box.unpack(data))
        elif type == FRAME_EXCEPTION:
            self.dispatch_exception(seq, self.box.unpack(data))
        else:
            raise ValueError("invalid frame type (%d)" % (type,))

    #
    # requests
    #
    def sync_request(self, handlername, *args):
        """performs a synchronous (blocking) request"""
        seq = self.send_request(handlername, *args)
        while seq not in self.sync_replies:
            self.serve()
        return self.sync_replies.pop(seq)
    
    def async_request(self, callback, handlername, *args):
        """performs an asynchronous (non-blocking) request"""
        seq = self.send_request(handlername, *args)
        self.async_replies[seq] = callback

    #
    # root requests (not through NetProxies)
    #
    def rimport(self, modulename):
        """imports a module by name (as a string)"""
        if modulename not in self.module_cache:
            module = self.sync_request("handle_import", modulename)
            self.module_cache[modulename] = module
        return self.module_cache[modulename]            

    def execute(self, expr, mode = "exec"):
        """executes the given code at the remote side of the connection"""
        return self.sync_request("handle_execute", expr, mode)

    #
    # handlers
    #
    def handle_decref(self, oid):
        self.box.decref(oid)
            
    def handle_delattr(self, oid, name):
        delattr(self.box[oid], name)

    def handle_getattr(self, oid, name):
        return getattr(self.box[oid], name)

    def handle_setattr(self, oid, name, value):
        setattr(self.box[oid], name, value)

    def handle_delitem(self, oid, index):
        del self.box[oid][index]

    def handle_getitem(self, oid, index):
        return self.box[oid][index]

    def handle_setitem(self, oid, index, value):
        self.box[oid][index] = value

    def handle_call(self, oid, args, kwargs):
        return self.box[oid](*args, **kwargs)

    def handle_repr(self, oid):
        return repr(self.box[oid])

    def handle_str(self, oid):
        return str(self.box[oid])

    def handle_bool(self, oid):
        return bool(self.box[oid])

    def handle_import(self, modulename):
        return __import__(modulename, None, None, modulename.split(".")[-1])

    def handle_getconn(self):
        return self

    def handle_execute(self, expr, mode):
        codeobj = compile(expr, "<from %s>" % (self,), mode)
        return eval(codeobj, self._local_namespace)



