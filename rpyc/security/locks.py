"""
Definition of a Lock for an object lock profile (olp), support routines
and/or predefined Locks
"""

from rpyc.lib.colls import MapTypeList

#A lock just implements permitted, which returns True or False
#or can also raise a SecurityException
class Lock(object):
    def permitted(self, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__

    def read_only_copy(self):
        return ReadLock(self)

#This is what is returned when you get a
#read only value.
class ReadLock(Lock):
    def __init__(self, other_lock):
        self._string_value = str(other_lock)

    def permitted(self, **kwargs):
        raise NotImplementedError("Cannot check permitted on read only lock")

    def __str__(self):
        return self._string_value

def sanitize_and_copy_lock_list(lock_list):
    if not isinstance(lock_list, (LockListAnd, LockListOr)):
        return LockListAnd(lock_list)
    return lock_list

def sanitize_lock_parameter(lock):
    if lock is None:
        lock=LL_And([])

    if isinstance(lock, Lock):
        lock=LL_And([lock])

    lock_list = sanitize_and_copy_lock_list(lock)
    return lock_list

def sanitize_lock_list_item(item, parent=None):
    if isinstance(item, Lock):
        return item

    else:
        try:
            item = sanitize_and_copy_lock_list(item)
        except TypeError:
            if parent is None:
                class_name = "A LockList"
            else:
                class_name = parent.__class__.__name__

            item_name = repr(item)
            error_tuple = (class_name, item_name)
            raise TypeError("%s does not allow %s to " % error_tuple
                          + "be stored, must be of type Lock, "
                          + "LockListAnd, LockListOr, or iterable "
                          + "accepted by LockListAnd constructor")
    return item

class LockListShared(MapTypeList):
    _join_text=", "

    def _map_item(self, item):
        item = sanitize_lock_list_item(item, parent=self)
        return item

    def __str__(self):
        string_list=[]
        for value in self:
            string_list.append(str(value))
        return "[" + self._join_text.join(string_list) +"]"

    def read_only_copy(self):
        return_value=self.__class__()
        for item in self:
            return_value.append( item.read_only_copy() )
        return return_value

#Marker class to say "and" these locks together
class LockListAnd(LockListShared):
    _join_text=" & "

#Marker class to say "or" these locks together
class LockListOr(LockListShared):
    _join_text=" | "

#Commonly used abbreviations:
LL_And = LockListAnd
LL_Or = LockListOr

class Blocked(Lock):
    def permitted( self, **kwargs ):
        return False

    def __str__(self):
        return "BLOCKED"

BLOCKED = Blocked()

class CollectionLock(Lock):
    def __init__(self, lock_list = LockListAnd()):
        lock_list = _sanitize_and_copy_lock_list(lock_list)
        self.locks = lock_list

    def permitted( self, **kwargs ):
        return self.locks

class PrefixLock(CollectionLock):
    def __init__(self, prefix, lock_list = LockListAnd()):
        super().__init__(lock_list)
        self.prefix = prefix

    def permitted( self, **kwargs ):
        if "name" in kwargs:
            if name.startswith(self.prefix):
                return super().permitted(**kwargs)
        return False

    def __str__(self):
        return self.__class__.__name__ + ":%s" % repr(self.prefix)

#same as rpyc_safeattrs but with the omission of __new__,
#and the addition of "__get__", "__set__", and "__delete__"
#be warned that some of these attrs traditionally do modification
#the the original object still. Typically they are only exposed
#by objects designed to do it those

#These are deprecated anyways:
#__getslice__ can expose writable list and or writeable parts
#__setslice__ obviously modifies.
#__delslice__ obviously modifies.

#These aren't:
#__getitem__ can expose writeable things from inside the object.
#__setitem__ can expose writeable things from inside the object.
#__delitem__ obviously modifies.
#__get__ exposes a possibly writeable attribute.
#__set__ obviously modifies
#__delete__ obviously modified (this is not __del__ btw)
#__next__ (python 3) and next (python 2) may expose writable things
#__iter__ can expose modifiable stuff.

SAFE_ATTRS = \
    set(['__int__', '__ror__', '__ipow__', '__lshift__', '__getslice__',
         '__ne__', '__str__', '__radd__', '__bool__', '__truediv__',
         '__rrshift__', '__irshift__', '__rdiv__', '__and__', '__lt__',
         '__abs__', '__rmod__', '__float__', '__rpow__', '__rand__',
         '__delslice__', '__iand__', '__invert__', '__contains__',
         '__rlshift__', '__cmp__', '__pos__', '__sub__', '__rfloordiv__',
         '__rsub__', '__rmul__', '__rshift__', '__enter__', '__ixor__',
         '__doc__', '__itruediv__', '__mul__', '__isub__', '__rdivmod__',
         '__exit__', '__getitem__', '__ifloordiv__', '__idiv__',
         '__next__', '__pow__', 'next', '__iter__', '__imod__',
         '__divmod__', '__add__', '__gt__', '__hex__', '__oct__', '__eq__',
         '__rxor__', '__ilshift__', '__delitem__', '__repr__',
         '__nonzero__', '__imul__', '__mod__', '__setslice__', '__neg__',
         '__setitem__', '__iadd__', '__xor__', '__ior__', '__div__',
         '__le__', '__len__', '__floordiv__',  '__hash__', '__index__',
         '__long__', '__rtruediv__', '__length_hint__', '__ge__', '__or__',
         '__get__', '__set__', '__delete__'])

class SafeAttrLock(CollectionLock):
    def __init__(self, prefix, lock_list = LockListAnd(),
                 safe_attrs = SAFE_ATTRS):
        super().__init__(lock_list)
        self.safe_attrs = safe_attrs

    def permitted( self, **kwargs ):
        if "name" in kwargs:
            if name in self.safe_attrs:
                return super().permitted( **kwargs )
        return False


