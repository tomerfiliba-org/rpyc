"""
The :mod:`rpyc.security.locks` module contains the definition of
:class:`Lock`, support routines, and/or predefined :class:`Lock`
implementations.

Rationale
---------

In some cases it makes sense to block use of `RPyC Exposed` objects and
classes with more precision. To that end this module supports the concept
of creating the ability to :class:`Lock` remote objects.

How the remote side is authenticated, and how you manage the security
of a remote application is up to the implementer.

A possible implementation would be to use Python threadlocal storage to
store a security profile for a user, and each remote connection gets its
own thread and security profile.

API
---

:class:`Lock` is an abstract class. You can inherit from it
and implement :meth:`permitted <Lock.permitted>` to check anything
you want.

:class:`Lock` is also passed useful information about what
is being accessed. An implementation can be used to log accesses to
objects.
"""

from rpyc.lib.colls import MapTypeList
from rpyc.lib.compat import basestring

#A lock just implements permitted, which returns True or False
#or can also raise a SecurityException
class Lock(object):
    """Abstract base class of all Lock objects"""
    def permitted(self, **kwargs):
        """Implement this method to check the lock
        The kwargs will be set as follows:

            * ``kwargs["access"]`` will be one of "getattr","setattr", or "delattr"

            * ``kwargs["instance"]`` will be the original instance
              (not the `RPyC Exposed` version)

            * ``kwargs["attribute"]`` will be the name of the attribute
              being accessed

            * ``kwargs["value"]`` will be present if
              ``kwargs["access"]=="setattr"``. It will be the value
              being set.

            * ``kwargs["wildcard"]`` will be ``None`` when not using wildcards.
              Otherwise, it will be the wildcard in the
              :class:`OLP <rpyc.security.olps.OLP>`
              that :class:`Lock` is being evaluated on.

        :return: True or False, or more locks
            to check (can be :class:`LockListShared`
            or simple iterable in which case a
            :class:`LockListAnd` is constructed from
            the iterable)
        """
        raise NotImplementedError()

    def __str__(self):
        """The __str__ implementation for Lock is useful for debugging
        purposes. The default implementation just prints the name
        of the :class:`Lock`.
        """
        return self.__class__.__name__

    def read_only_copy(self):
        """This returns a read only representation of the lock.
        This is what the remote side gets when it tries to see
        what locks are present.

        The default is to use :class:`ReadLock` to create
        a lock that is not useable, but whose :meth:`__str__`
        method returns the same string as the original
        lock.

        .. note ::

            The returned value must also be of a type that is a subclass of
            :class:`Lock` even if non-functional. If it is not of this type
            :meth:`read_only_copy <rpyc.security.olps.OLP.read_only_copy>`
            of :class:`OLP <rpyc.security.olps.OLP>` will not work because
            the "read only lock" will not be storable in a
            :class:`LockListShared`.

        ..
        """
        return ReadLock(self)

#This is what is returned when you get a
#read only value.
class ReadLock(Lock):
    """Construct a ReadLock from a Lock if
    you want a lock that can't be used, but
    which the remote side can look at via
    :meth:`__str__`.
    """
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
    """This is an abstract base class of :class:`LockListAnd` and
    :class:`LockListOr`. Do not use this class, you must use
    :class:`LockListAnd` or :class:`LockListOr` instead.

    A :class:`LockListShared` implemtnes a list of
    :class:`Lock` and :class:`LockListShared` items.
    It operates essentially the same way as :class:`list`
    does in Python, except:

        * It only accepts :class:`Lock` and  :class:`LockListShared`
          as its members. You can also assign an iterable sequence
          and it will be converted into a :class:`LockListAnd`

        * It can be used to build boolean expressions.
          Depending on whether an instance of
          :class:`LockListShared` is a :class:`LockListAnd`
          or a :class:`LockListOr` it is considered to
          represent a boolean ``and`` or ``or`` of its
          items respectively. Nesting these can be
          used to build complex boolean expressions.

        * An empty :class:`LockListAnd` is considered
          to evaluate to `True`, an empty :class:`LockListOr`
          if considered to evaluate to ``False``

    Almost all parameters in the security api that take a ``Lock``
    will also accept an arbitrary :class:`LockListShared`

    They will also usually accept any iterable suitable
    for passing to the :class:`LockListAnd` constructor. Passing
    one of these to such a parameter is the same as passing:
    :class:`LockListAnd(value) <LockListAnd>`

    The constructor operates the same way the Python :class:`list`
    constructor works, except it rejects illegal items.
    """

    _join_text=", "
    _no_items_str=""

    def _map_item(self, item):
        raise NotImplementedError()

    def __str__(self):
        string_list=[]
        for value in self:
            string_list.append(str(value))
        if len(string_list) == 0:
            return self._no_items_str

        return "[" + self._join_text.join(string_list) +"]"

    def read_only_copy(self):
        return_value=self.__class__()
        for item in self:
            return_value.append( item.read_only_copy() )
        return return_value

#Marker class to say "and" these locks together
class LockListAnd(LockListShared):
    """List of locks and/or LockListShared elements.
    This represents a boolean ``and`` of the lock
    elements. This implements :class:`LockListShared`.

    An :class:`LockListAnd` is considered to evaluate
    to True if all of its members evaluate to ``True``.

    An empty :class:`LockListAnd` is considered
    to evaluate to ``True``.

    Calling :meth:`__str__` on this class yields
    a representation that looks like the one for Python's
    :class:`list` class, except instead of commas, there
    will be "&" signs.

    The constructor operates the same way the Python :class:`list`
    constructor works, except it rejects illegal items.
    """

    def _map_item(self, item):
        item = sanitize_lock_list_item(item, parent=self)
        return item

    _join_text=" & "
    _no_items_str="True"

#Marker class to say "or" these locks together
class LockListOr(LockListShared):
    """List of locks and/or LockListShared elements.
    This represents a boolean ``or`` of the lock
    elements. This implements :class:`LockListShared`.

    An :class:`LockListOr` is considered to evaluate
    to True if any of its members evaluate to ``True``.

    An empty :class:`LockListOr` is considered
    to evaluate to ``False``.

    Calling :meth:`__str__` on this class yields
    a representation that looks like the one for Python's
    :class:`list` class, except instead of commas, there
    will be "|" signs.

    The constructor operates the same way the Python :class:`list`
    constructor works, except it rejects illegal items.
    """

    def _map_item(self, item):
        item = sanitize_lock_list_item(item, parent=self)
        return item

    _join_text=" | "
    _no_items_str="False"

#Commonly used abbreviations:
LL_And = LockListAnd

LL_Or = LockListOr

class Blocked(Lock):
    """This is the implementation of a Lock that is always blocked.
    """
    def permitted( self, **kwargs ):
        return False

    def __str__(self):
        return "BLOCKED"

BLOCKED = Blocked()
"""BLOCKED is an instance of :class:`Blocked` that can be used in
user code.
"""

class CollectionLock(Lock):
    """:class:`CollectionLock` is an implementation
    of :class:`Lock`  that acts as a single lock but is in
    actuality multiple locks.

    Since most ``lock`` parameters accept
    :class:`LockListShared` lists already, this is
    mainly designed to be inherited by other
    :class:`Lock` implementations to allow them to
    store a :class:`LockListShared` expression
    to evaluate should some other condition
    be met.

    :param lock: A :class:`Lock`, :class:`LockListShared`,
        or an iterable suitable to passed into
        :class:`LockListAnd` constructor

    Whatever ``lock`` is will be evaluated in its entirety
    when :meth:`permitted` is called.

    By default ``lock`` is an empty :class:`LockListAnd'
    which will always evaluate as ``True``.
    """
    def __init__(self, lock = []):
        lock_list = sanitize_lock_parameter(lock)
        self.locks = lock_list

    def permitted( self, **kwargs ):
        return self.locks

    def __str__(self):
        return "CollectionLock(%s)" % self.locks

class PrefixLock(CollectionLock):
    """:class:`PrefixLock` is a :class:`CollectionLock`
    subclass that can be used to check to see if the
    name of the attribute being fetched has a certain
    prefix.

    It basically can be used to mimic the behavior
    of the :ref:`RPyC protocol <api-protocol>`
    ``exposed_prefix`` parameter, but on a case
    by case business. It is meant for use
    with :class:`OLP <rpyc.security.olps.OLP>` wildcards.
    It will not work for calling
    functions and methods unless `allow_unsafe_calls` is enabled
    in the :ref:`RPyC protocol <api-protocol>`

    :param lock: A :class:`Lock`, :class:`LockListShared`,
        or an iterable suitable to passed into
        :class:`LockListAnd` constructor
    :param str prefix: A prefix string that a field
        or method must start with in order for the :class:`PrefixLock`
        to not be blocked

    If the ``prefix`` is found, then ``lock`` is checked.
    By default ``lock`` is an empty :class:`LockListAnd`
    which will always evaluate as ``True``.
    """
    def __init__(self, lock=[], prefix="exposed_"):
        lock_list = sanitize_lock_parameter(lock)

        if not isinstance(prefix, basestring): #basestring from compat
                                               #library
            raise TypeError("prefix must be a string.")

        super(PrefixLock, self).__init__(lock_list)
        self.prefix = prefix

    def permitted( self, **kwargs ):
        name = kwargs['attribute']
        if name.startswith(self.prefix):
            return super(PrefixLock, self).permitted(**kwargs)
        return False

    def __str__(self):
        return "PrefixLock(%s, %s)" % (self.prefix, self.locks)

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
         '__long__', '__rtruediv__', '__length_hint__', '__ge__', '__or__'])
"""This is a list of "safe" attributes that is *almost* identical to the default allowed
list of so called 'safe' attributes associated with ``allow_safe_attrs``
in the :ref:`RPyC protocol <api-protocol>` protocol configuration.
The attribute *__new__* has been removed from the list.

Note that there is very little that is safe about this list.
All these method calls can have side effects, but the following are particularly
dangerous:

    * :meth:`__getitem__` can expose writeable things from inside the object.
    * :meth:`__setitem__` can modify the object in unwanted ways.
    * :meth:`__delitem__` can allow unwanted deltions.
    * :meth:`__next__` (Python 3) / :meth:`next` (Python 2) may expose writable subobjects
    * :meth:`__iter__` can expose writable subobjects.

These deprecated functions can be dangerous in Python 2:
    * :meth:`__getslice__` can expose writable list and or writeable parts
    * :meth:`__setslice__` can modify the object in unwanted ways.
    * :meth:`__delslice__` can allow unwanted deletions.

This method of access is extremely dangerous and generally should not be
used.
"""

class SafeAttrLock(CollectionLock):
    """SafeAttrLock(lock=[], safe_attrs=SAFE_ATTRS)

    SafeAttrLock is a :class:`CollectionLock` subclass
    that can be used to check to see if the name of the
    attribute being fetched is in a list of predefined
    "safe" attributes.

    It basically can be used to mimic the behavior
    of the :ref:`RPyC protocol <api-protocol>`
    ``safe_attrs`` parameter, but on a case
    by case business. It is meant for use
    with :class:`OLP <rpyc.security.olps.OLP>` wildcards.
    It will not work for calling
    functions and methods unless `allow_unsafe_calls` is enabled
    in the :ref:`RPyC protocol <api-protocol>`

    :param lock: A :class:`Lock`, :class:`LockListShared`,
        or an iterable suitable to passed into
        :class:`LockListAnd` constructor
    :param set safe_attrs: A set of attribute names to consider
        "*safe*"

    If the ``prefix`` is found, then ``lock`` is checked.
    By default ``lock`` is an empty :class:`LockListAnd`
    which will always evaluate as ``True``.
    """
    def __init__(self, lock = [],
                 safe_attrs = SAFE_ATTRS):

        lock_list = sanitize_lock_parameter(lock)

        super(SafeAttrLock, self).__init__(lock_list)
        self.safe_attrs = safe_attrs

    def permitted( self, **kwargs ):
        name = kwargs["attribute"]
        if name in self.safe_attrs:
            return super(SafeAttrLock, self).permitted( **kwargs )
        return False

    def __str__(self):
        return "SafeAttrLock(%s)" % self.locks


