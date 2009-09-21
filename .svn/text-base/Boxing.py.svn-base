import sys
import traceback
import cPickle as pickle
from weakref import WeakValueDictionary
from Lib import ImmDict
from NetProxy import NetProxy, SyncNetProxy, _get_conn, _get_oid
from Lib import orig_isinstance


class BoxingError(Exception):
    pass
class NestedException(Exception): 
    pass

PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL
TYPE_SIMPLE = 0
TYPE_PROXY = 1
TYPE_TUPLE = 2
TYPE_SLICE = 3
TYPE_LOCAL_PROXY = 4
TYPE_IMMDICT = 5
simple_types = (
    bool, 
    int, 
    long, 
    float, 
    complex, 
    basestring, 
    type(None),
)

def dump_exception(typ, val, tb):
    """dumps the given exception using pickle (since not all exceptions are picklable)"""
    tbtext = "".join(traceback.format_exception(typ, val, tb))
    sys.last_type, sys.last_value, sys.last_traceback = typ, val, tb
    try:
        pickled_exc = pickle.dumps((typ, val, tbtext), protocol = PICKLE_PROTOCOL)
    except pickle.PicklingError, ex:
        newval = NestedException("pickling error %s\nexception type: %r\nexception object: %s" % (ex, typ, val))
        pickled_exc = pickle.dumps((NestedException, newval, tbtext), protocol = PICKLE_PROTOCOL)
    return pickled_exc

def load_exception(package):
    """returns an exception object"""
    try:
        return pickle.loads(package)
    except pickle.PicklingError, ex:
        return NestedException("failed to unpickle remote exception -- %r" % (ex,))

class Box(object):
    """a box is where local objects are stored, and remote proxies are created"""
    __slots__ = ["conn", "objects", "proxy_cache"]
    
    def __init__(self, conn):
        self.conn = conn
        self.objects = {}
        self.proxy_cache = WeakValueDictionary()

    def close(self):
        del self.conn
        del self.objects
        del self.proxy_cache
    
    def __getitem__(self, oid):
        return self.objects[oid][1]

    def _box(self, obj):
        if orig_isinstance(obj, simple_types):
            return TYPE_SIMPLE, obj
        elif orig_isinstance(obj, slice):
            return TYPE_SLICE, (obj.start, obj.stop, obj.step)
        elif orig_isinstance(obj, NetProxy) and _get_conn(obj) is self.conn:
            return TYPE_LOCAL_PROXY, _get_oid(obj)
        elif orig_isinstance(obj, tuple):
            if obj:
                return TYPE_TUPLE, [self._box(subobj) for subobj in obj]
            else:
                return TYPE_SIMPLE, ()
        elif orig_isinstance(obj, ImmDict):
            if not obj.dict:
                return TYPE_SIMPLE, {}
            else:
                return TYPE_IMMDICT, [(self._box(k), self._box(v)) for k, v in obj.items()]
        else:
            oid = id(obj)
            self.objects.setdefault(oid, [0, obj])[0] += 1
            return TYPE_PROXY, oid

    def _unbox(self, (type, value)):
        if type == TYPE_SIMPLE:
            return value
        elif type == TYPE_TUPLE:
            return tuple(self._unbox(subobj) for subobj in value)
        elif type == TYPE_SLICE:
            return slice(*value)
        elif type == TYPE_LOCAL_PROXY:
            return self[value]
        elif type == TYPE_IMMDICT:
            return dict((self._unbox(k), self._unbox(v)) for k, v in value)
        elif type == TYPE_PROXY:
            if value in self.proxy_cache:
                proxy = self.proxy_cache[value]
            else:
                proxy = SyncNetProxy(self.conn, value)
                self.proxy_cache[value] = proxy
            return proxy
        else:
            raise BoxingError("invalid boxed object type", type, value)
        
    def decref(self, oid):
        self.objects[oid][0] -= 1
        if self.objects[oid][0] <= 0:
            del self.objects[oid]
    
    def pack(self, obj):
        """packs an object (returns a package)"""
        return pickle.dumps(self._box(obj), protocol = PICKLE_PROTOCOL)

    def unpack(self, package):
        """unpacks a package (returns an object)"""
        return self._unbox(pickle.loads(package))


