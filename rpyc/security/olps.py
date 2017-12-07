"""
The :mod:`rpyc.security.olps` contains the definition of
:class:`OLP`, otherwise known as an object lock profile.

An object lock profile specifies what attributes can
be remotely accessed for a `RPyC Exposed`
class and its instances.
"""

import types

from rpyc.lib.compat import is_py3k
from rpyc.lib.colls import MapTypeDict
from rpyc.security import locks
from rpyc.security.exceptions import SecurityError, SecurityAttrError

if not is_py3k:
    import keyword
    import re

#MERGE modification types
MERGE_REPLACE = 0
MERGE_AND = 1
MERGE_OR = 2

def is_identifier(value):
    if is_py3k:
        return isinstance(value, str) and value.isidentifier()
    else:
        if not isinstance(value, basestring):
            return False
        try:
            value = str(value)
        except UnicodeEncodeError:
            return False
        if keyword.iskeyword(value):
            return False
        return re.match(r'^[a-z_][a-z0-9_]*$', value, re.I) is not None

def is_attr_wildcard(key):
    return key in ["&", "|", "*"]

def sanitize_attr_key(key):
    if not is_attr_wildcard(key):
        if not is_identifier(key):
            raise ValueError("Attribute key %s is invalid--" % repr(key)
                             + "it is not a valid identifier")
    return key

class LockAttrDictionary(MapTypeDict):
    """Implementation of :class:`dict` that:

        * Only allows wildcards and valid Python
           identifier strings as keys.
        * Only allows
          :class:`LockListShared <rpyc.security.locks.LockListShared>`
          values as items.

        The constructor has the same interface as :class:`dict`
    """

    def _map_key(self, key):
        key = sanitize_attr_key(key)
        return key

    def _map_item(self, item):
        item = locks.sanitize_lock_parameter(item)
        return item

    def read_only_copy(self):
        return_value = LockAttrDictionary()
        for key in list(self.keys()):
            return_value[key] = self[key].read_only_copy()
        return return_value

    def __str__(self):
        output=""
        for key in sorted(list(self.keys())):
            output += "\t%s: %s\n" % (key, str(self[key]))
        return output

def LAD(value):
    #Use this when we really want to
    #check out arguments.
    if isinstance(value, LockAttrDictionary):
        return value
    else:
        return LockAttrDictionary(value)

#The values stored from getattr_locks, setattr_locks,
#delattr_locks, etc...they are LIVE values, they can
#be changed. To that extend, this code should never
#append or changes those values, just replace or wrap them
class OLP(object):
    """Object Lock Profile Class (OLP) class

    An :class:`OLP` specifies what attributes can be
    remotely accessed via :meth:`_rpyc_getattr`,
    :meth:`_rpyc_setattr`, and :meth:`_rpyc_delattr`
    for a `RPyC Exposed` class and its instances.

    :param getattr_locks: A :class:`LockAttrDictionary` or value for
        which ``LockAttrDictionary(value)`` works
    :param setattr_locks: A :class:`LockAttrDictionary` or value for
        which ``LockAttrDictionary(value)`` works
    :param delattr_locks: A :class:`LockAttrDictionary` or value for
        which ``LockAttrDictionary(value)`` works
    :param cls_getattr_locks: A :class:`LockAttrDictionary` or value for
        which ``LockAttrDictionary(value)`` works
    :param cls_setattr_locks: A :class:`LockAttrDictionary` or value for
        which ``LockAttrDictionary(value)`` works
    :param cls_delattr_locks: A :class:`LockAttrDictionary` or value for
        which ``LockAttrDictionary(value)`` works
    :param bool lock_local: Used for currently unimplemented feature
    :param bool mark: Set this to ``True`` or ``False`` to indicate
        whether ``repr(instance)`` will mark instances with "RPyC exposed"

    All these parameters are optional.

    Conceptually use of this class is very simple.

    Associated with each :class:`OLP` are a set of dictionaries.
    Each of these dictionaries is known as a
    :class:`LockAttrDictionary` or
    :class:`LAD <LockAttrDictionary>`
    Each of these dictionaries is in charge of
    a different type of access:

        * ``getattr_locks`` is in charge of get accesses to instances
        * ``setattr_locks`` is in charge of set accesses to instances
        * ``delattr_locks`` is in charge of del accesses to instances
        * ``cls_getattr_locks`` is in charge of get accesses to the class
        * ``cls_setattr_locks`` is in charge of set accesses to the class
        * ``cls_delattr_locks`` is in charge of del accesses to the class

    The keys of each dictionary are the names of accessible attributes.

    If a key doesn't exist, it isn't accessible.

    Each item stored in a key slot is a
    :class:`LockListShared <rpyc.security.locks.LockListShared>`
    representing a boolean expression of
    :class:`Lock <rpyc.security.locks.Lock>` types that must
    evaluate to ``True`` in order to access that attribute.

    Additionally the keys "*", "&", and "|" can be present in a
    :class:`LockAttrDictionary` to allow special wildcard based access.

    Access checking proceeds as follows::

        (check_locks(attribute_name) and check_locks('&')) or check_locks('|')

    That is, any :class:`LockListShared` stored with the "&" wildcard key
    can be used to impose additional constraints for all attribute accesses
    of a type.

    A :class:`LockListShared` stored to the "|" wildcard key can be used
    to bypass normal access for a specific type of access.

    The '*' wildcard only comes into play only if an attribute name is not
    found in the :class:`LockAttrDictionary`. Normally a missing attribute
    name makes the first term in the parenthesis of the expression above
    automatically ``False``. However the `*` wildcard can be used to
    specify locks to use for accessing attributes missing from the
    :class:`LockAttrDictionary`.

    .. note ::

        Each :class:`LockAttrDictionary` specified by the constructor
        will be copied before being stored internally. The copies will be
        a deep copy of everything but the :class:`Lock` values themselves.
    """
    def __init__(self, getattr_locks = dict(),
                       setattr_locks = dict(),
                       delattr_locks = dict(),
                       cls_getattr_locks = dict(),
                       cls_setattr_locks = dict(),
                       cls_delattr_locks = dict(),
                       lock_local = False,
                       mark = True ):

        self._push = None #Used for chaining "pushed" profiles.

        self.wipe() #Must be done in case some parameters have none passed.

        self._lock_local = bool(lock_local)
        self._mark = mark

        self.replace(getattr_locks,
                     setattr_locks,
                     delattr_locks,
                     cls_getattr_locks,
                     cls_setattr_locks,
                     cls_delattr_locks)

    #Makes nothing readable, but no locks included
    def wipe(self):
        """Replaces all the :class:`LockAttrDictionary`
        items associated with the :class:`OLP` with
        empty ones, making nothing accessible.
        """
        self.replace(getattr_locks = dict(),
                     setattr_locks = dict(),
                     delattr_locks = dict(),
                     cls_getattr_locks = dict(),
                     cls_setattr_locks = dict(),
                     cls_delattr_locks = dict())

    @staticmethod
    def _wipe_attr_locks( attrs, wipe_attr_iterable ):
        if wipe_attr_iterable is not None:
            for key in wipe_attr_iterable:
                key = sanitize_attr_key(key)
                try:
                    del(attrs[key])
                except KeyError:
                    pass #Already wiped.

    def wipe_specified(self, getattr_locks = set(),
                             setattr_locks = set(),
                             delattr_locks = set(),
                             cls_getattr_locks = set(),
                             cls_setattr_locks = set(),
                             cls_delattr_locks = set()):
        """Used to remove access associated with identifiers
        and wildcards on a case by case basis.

        :param getattr_locks: A :class:`set` of specified Python identifiers and/or
            wildcards to wipe from the internal ``getattr_locks``
            :class:`LockAttrDictionary`
        :param setattr_locks: A :class:`set` of specified Python identifiers and/or
            wildcards to wipe from the internal ``setattr_locks``
            :class:`LockAttrDictionary`
        :param delattr_locks: A :class:`set` of specified Python identifiers and/or
            wildcards to wipe from the internal ``delattr_locks``
            :class:`LockAttrDictionary`
        :param cls_getattr_locks: A :class:`set` of specified Python identifiers and/or
            wildcards to wipe from the internal ``cls_getattr_locks``
            :class:`LockAttrDictionary`
        :param cls_setattr_locks: A :class:`set` of specified Python identifiers and/or
            wildcards to wipe from the internal ``cls_setattr_locks``
            :class:`LockAttrDictionary`
        :param cls_delattr_locks: A :class:`set` of specified Python identifiers and/or
            wildcards to wipe from the internal ``cls_delattr_locks``
            :class:`LockAttrDictionary`

        Any identifier of wildcard found in one of these :class:`set` values will be
        wiped from the associated internal :class:`LockAttrDictionary`.

        These are all empty by default which means nothing will be wiped.
        """
        self._wipe_attr_locks(self.getattr_locks, getattr_locks)
        self._wipe_attr_locks(self.setattr_locks, setattr_locks)
        self._wipe_attr_locks(self.delattr_locks, delattr_locks)
        self._wipe_attr_locks(self.cls_getattr_locks, cls_getattr_locks)
        self._wipe_attr_locks(self.cls_setattr_locks, cls_setattr_locks)
        self._wipe_attr_locks(self.cls_delattr_locks, cls_delattr_locks)

    #Makes nothing readable, but no locks included
    def wipe_name(self, name):
        """Used to remove entries with the key of ``name`` from
        all six internal :class:`LockAttrDictionary` values, making
        `name` completely inaccessible (except possibly by wildcard).

        :param str name: Name of identifier or wildcard to be removed
            from :class:`OLP`
        """

        value = set([name])
        self.wipe_specified(getattr_locks = value,
                            setattr_locks = value,
                            delattr_locks = value,
                            cls_getattr_locks = value,
                            cls_setattr_locks = value,
                            cls_delattr_locks = value)

    def replace(self, getattr_locks = None,
                      setattr_locks = None,
                      delattr_locks = None,
                      cls_getattr_locks = None,
                      cls_setattr_locks = None,
                      cls_delattr_locks = None):
        """Used to replace one or more internal
        :class:`LockAttrDictionary` values.

        :param getattr_locks: A :class:`LockAttrDictionary`, a value for
            which ``LockAttrDictionary(value)`` works, or None
        :param setattr_locks: A :class:`LockAttrDictionary`, a value for
            which ``LockAttrDictionary(value)`` works, or None
        :param delattr_locks: A :class:`LockAttrDictionary`, a value for
            which ``LockAttrDictionary(value)`` works, or None
        :param cls_getattr_locks: A :class:`LockAttrDictionary`, a value for
            which ``LockAttrDictionary(value)`` works, or None
        :param cls_setattr_locks: A :class:`LockAttrDictionary`, a value for
            which ``LockAttrDictionary(value)`` works, or None
        :param cls_delattr_locks: A :class:`LockAttrDictionary`, a value for
            which ``LockAttrDictionary(value)`` works, or None

        Any parameter which isn't ``None`` will replace the internal
        specified :class:`LockAttrDictionary`.

        .. note ::

            Each :class:`LockAttrDictionary` specified in :meth:`replace`
            will be copied before being stored internally. The copies will be
            a deep copy of everything but the :class:`Lock` values themselves.
        """
        if getattr_locks is not None:
            self.getattr_locks = LAD(getattr_locks)

        if setattr_locks is not None:
            self.setattr_locks = LAD(setattr_locks)

        if delattr_locks is not None:
            self.delattr_locks = LAD(delattr_locks)

        if cls_getattr_locks is not None:
            self.cls_getattr_locks = LAD(cls_getattr_locks)

        if cls_setattr_locks is not None:
            self.cls_setattr_locks = LAD(cls_setattr_locks)

        if cls_delattr_locks is not None:
            self.cls_delattr_locks = LAD(cls_delattr_locks)

    @staticmethod
    def _merge_replace(old_attrs, new_attrs):
        return new_attrs

    @staticmethod
    def _merge_and(old_attrs, new_attrs):
        return locks.LockListAnd([old_attrs, new_attrs])

    @staticmethod
    def _merge_or(old_attrs, new_attrs):
        return locks.LockListOr([old_attrs, new_attrs])

    def _merge_attr_locks(self, attrs=None, new_attrs=None, merger=None):
        if new_attrs is not None:
            new_attrs = LAD(new_attrs)
            for key in new_attrs:
                if key not in attrs:
                    attrs[key] = new_attrs[key]
                else:
                    attrs[key] = merger( attrs[key],
                                         new_attrs[key] )

    def merge_specified(self, merge_mode = MERGE_AND,
                         getattr_locks = {},
                         setattr_locks = {},
                         delattr_locks = {},
                         cls_getattr_locks = {},
                         cls_setattr_locks = {},
                         cls_delattr_locks = {}):
        """Used to merge other :class:`LockAttrDictionary` values
        into the :class:`OLP`.

        :param merge_mode: Specifies how the data will be merged
        :param getattr_locks: A :class:`LockAttrDictionary`, or a value for
            which ``LockAttrDictionary(value)`` works
        :param setattr_locks: A :class:`LockAttrDictionary`, or a value for
            which ``LockAttrDictionary(value)`` works
        :param delattr_locks: A :class:`LockAttrDictionary`, or a value for
            which ``LockAttrDictionary(value)`` works
        :param cls_getattr_locks: A :class:`LockAttrDictionary`, or a value for
            which ``LockAttrDictionary(value)`` works
        :param cls_setattr_locks: A :class:`LockAttrDictionary`, or a value for
            which ``LockAttrDictionary(value)`` works
        :param cls_delattr_locks: A :class:`LockAttrDictionary`, or a value for
            which ``LockAttrDictionary(value)`` works

        For each of the :class:`LockAttrDictionary` parameters, the keys
        of that :class:`LockAttrDictionary` are iterated over. If the key
        doesn't exist in the associated internal :class:`LockAttrDictionary`,
        it is added::

            internal[key] = parameter[key]

        If a value already *does* exist internally, the information
        from ``internal[key]`` is *merged* with the information
        from ``parameter[key]``.

        The merge can be one of several different types, specified by
        the `merge_mode` parameter:

            * :data:`MERGE_REPLACE` specifies::

                internal[key] = parameter[key]

            * :data:`MERGE_AND` specifies::

               internal[key] = LockListAnd(internal[key], parameter[key])

            * :data:`MERGE_OR` specifies::

               internal[key] = LockListOr(internal[key], parameter[key])

        .. note ::

            All provided parameter data is copied. The copies will be
            a deep copy of everything but the :class:`Lock` values themselves.
        """
        if merge_mode == MERGE_REPLACE:
            merger = self._merge_replace
        elif merge_mode == MERGE_AND:
            merger = self._merge_and
        elif merge_mode == MERGE_OR:
            merger = self._merge_or
        else:
            raise ValueError("Illegal merge_mode value")

        self._merge_attr_locks(self.getattr_locks, getattr_locks, merger)
        self._merge_attr_locks(self.setattr_locks, setattr_locks, merger)
        self._merge_attr_locks(self.delattr_locks, delattr_locks, merger)
        self._merge_attr_locks(self.cls_getattr_locks,
                               cls_getattr_locks, merger)
        self._merge_attr_locks(self.cls_setattr_locks,
                               cls_setattr_locks, merger)
        self._merge_attr_locks(self.cls_delattr_locks,
                               cls_delattr_locks, merger)


    #Will only replace attr locks if there is a key.
    def replace_specified(self, **kwargs):
        """Shorthand for::

            self.merge_specified(merge_mode=MERGE_REPLACE, **kwargs)

        ..
        """
        self.merge_specified(merge_mode = MERGE_REPLACE,
                             **kwargs)

    def and_specified(self, **kwargs):
        """Shorthand for::

            self.merge_specified(merge_mode=MERGE_AND, **kwargs)

        ..
        """
        self.merge_specified(merge_mode = MERGE_AND,
                             **kwargs)

    def or_specified(self, **kwargs):
        """Shorthand for::

            self.merge_specified(merge_mode=MERGE_OR, **kwargs)

        ..
        """
        self.merge_specified(merge_mode = MERGE_OR,
                            **kwargs)

    def and_olp(self, other):
        """this performs an :meth:`and_specified`
        over all six :class:`LockAttrDictionary` values of the
        `other` parameter merging its data into our self.

        :param OLP other: the other :class:`OLP` to merge in.

        using `and_olp` to merge in usually does the right thing,
        but may not be what is desired in particular if wildcards
        are in use.
        """
        if not isinstance(other, OLP):
            raise ValueError("other is not an OLP")

        self.and_specified(getattr_locks = other.getattr_locks,
                           setattr_locks = other.setattr_locks,
                           delattr_locks = other.delattr_locks,
                           cls_getattr_locks = other.getattr_locks,
                           cls_setattr_locks = other.cls_setattr_locks,
                           cls_delattr_locks = other.cls_delattr_locks)

    def or_olp(self, other):
        """this performs an :meth:`or_specified`
        over all six :class:`LockAttrDictionary` values of the
        `other` parameter merging its data into our self.

        :param OLP other: the other :class:`OLP` to merge in.
        """
        self.or_specified(getattr_locks = other.getattr_locks,
                          setattr_locks = other.setattr_locks,
                          delattr_locks = other.delattr_locks,
                          cls_getattr_locks = other.cls_getattr_locks,
                          cls_setattr_locks = other.cls_setattr_locks,
                          cls_delattr_locks = other.cls_delattr_locks)

    def total_expose(self, lock=[], wildcard="|"):
        """This is a convenience function to totally expose
        an :class:`OLP`.

        :param lock: :class:`Lock <rpyc.security.locks.Lock>`,
            :class:`LockListShared <rpyc.security.locks.LockListShared>`,
            or an iterable suitable to be passed into
            :class:`LockListAnd <rpyc.security.locks.LockListAnd>`
            constructor

        :param wildcard: '*', '&', or '|'

        This uses :meth:`or_specified` to merge::

            LockAttrDictionary({wildcard:lock})

        Into all six internal :class:`LockAttrDictionary`
        values.

        Using "*" exposes anything that isn't already
        exposed with the lock(s) of ``lock``.

        Using "|" exposes anything with the lock(s) of
        ``lock``.

        Using "&" adds the need to pass the lock(s)
        of ``lock`` to access anything (at least
        anything that does not have an alternate "|" wildcard
        accessor)
        """
        lock_list = locks.sanitize_lock_parameter(lock)

        if not wildcard in "*&|":
            raise ValueError("wildcard must be '*', '&', or '|'")

        getattr_locks = {wildcard:lock_list}
        setattr_locks = {wildcard:lock_list}
        delattr_locks = {wildcard:lock_list}
        cls_getattr_locks = {wildcard:lock_list}
        cls_setattr_locks = {wildcard:lock_list}
        cls_delattr_locks = {wildcard:lock_list}

        self.or_specified(getattr_locks = getattr_locks,
                          setattr_locks = setattr_locks,
                          delattr_locks = delattr_locks,
                          cls_getattr_locks = cls_getattr_locks,
                          cls_setattr_locks = cls_setattr_locks,
                          cls_delattr_locks = cls_delattr_locks)

    def read_expose(self, lock=[], wildcard="|"):
        """This is a convenience function to make every attribute
        :meth:`_rpyc_getattr`` accessible for an :class:`OLP`.

        :param lock: :class:`Lock <rpyc.security.locks.Lock>`,
            :class:`LockListShared <rpyc.security.locks.LockListShared>`,
            or an iterable suitable to be passed into
            :class:`LockListAnd <rpyc.security.locks.LockListAnd>`
            constructor

        :param wildcard: '*', '&', or '|'

        This uses :meth:`or_specified` to merge::

            LockAttrDictionary({wildcard:lock})

        Into ``getattr_locks`` and ``cls_getattr_locks``.

        Using "*" exposes anything for reading that isn't already
        exposed with the lock(s) of ``lock``.

        Using "|" exposes anything for reading with the lock(s) of
        ``lock``.

        Using "&" adds the need to pass the lock(s)
        of ``lock`` to read anything (at least
        anything that does not have an alternate "|" wildcard
        accessor)
        """
        lock_list = locks.sanitize_and_copy_lock_list(lock)

        if not wildcard in "*&|":
            raise ValueError("wildcard must be '*', '&', or '|'")

        getattr_locks = {wildcard:lock_list}
        cls_getattr_locks = {wildcard:lock_list}

        self.or_specified(getattr_locks = getattr_locks,
                          cls_getattr_locks = cls_getattr_locks)


    def push(self):   #Stores copy of self on stack to pop to.
        """Convenience function that pushes copy of entire
        :class:`OLP` :class:`LockAttrDictionary` state into an
        internal stack. It can then be modified temporarily,
        used, and restored with a :meth:`pop`
        """

        self._push = ( self.copy(self, include_stack = True))

        #new version should be copy, a deepcopy, using replace does the
        #appropriate copying.
        self.replace(getattr_locks = self.getattr_locks,
                     setattr_locks = self.setattr_locks,
                     delattr_locks = self.delattr_locks,
                     cls_getattr_locks = self.cls_getattr_locks,
                     cls_setattr_locks = self.cls_setattr_locks,
                     cls_delattr_locks = self.cls_delattr_locks)

    def pop(self):
        """Convenience function that restores copy of entire
        :class:`OLP` :class:`LockAttrDictionary` state from
        head of internal stack, if previously :meth:`push`
        was called.

        :raises SecurityError: if stack is empty.
        """

        if self._push is None:
            raise SecurityError("OLP stack underflow--too many OLP.pop() calls")
        self._copy_into(self, self._push, include_stack = True)

    def _copy_into(self, other, include_stack = False):
        self.getattr_locks = LAD(other.getattr_locks)
        self.setattr_locks = LAD(other.setattr_locks)
        self.delattr_locks = LAD(other.delattr_locks)
        self.cls_getattr_locks = LAD(other.cls_getattr_locks)
        self.cls_setattr_locks = LAD(other.cls_setattr_locks)
        self.cls_delattr_locks = LAD(other.cls_delattr_locks)
        self._lock_local = other._lock_local
        self._mark = other._mark

        if include_stack:
            self._push = self.copy(other._push, include_stack = True)
        else:
            self._push = None

    def copy(self, include_stack = False):
        """Create an identical copy of this `OLP`

        :param bool include_stack: Whether to copy the internal
            stack state

        Creates new :class:`OLP` that is a deep copy of this
        one, except for the
        :class:`Lock <rpyc.security.locks.Lock>` values themselves.

        the internal stack of :class:`OLP` states is not
        copied (new value has empty stack)
        unless ``include_stack`` is ``True``
        """

        new_value = self.__class__()
        new_value._copy_into( self, include_stack = include_stack )

        return new_value

    def read_only_copy(self):
        """Create 'read only copy' of :class:`OLP`

        Creates new :class:`OLP` that is a deep copy of this
        one (except not including internal stack state).

        However, all :class:`Lock <rpyc.security.locks.Lock>` values are
        replaced with whatever they return when their
        :meth:`read_only_copy` method is called.

        The internal stack state (if any) is not copied.
        """
        new_value = self.__class__()
        new_value.getattr_locks = self.getattr_locks.read_only_copy()
        new_value.setattr_locks = self.setattr_locks.read_only_copy()
        new_value.delattr_locks = self.delattr_locks.read_only_copy()
        new_value.cls_getattr_locks = self.cls_getattr_locks.read_only_copy()
        new_value.cls_setattr_locks = self.cls_setattr_locks.read_only_copy()
        new_value.cls_delattr_locks = self.cls_delattr_locks.read_only_copy()
        new_value._lock_local = self._lock_local
        new_value._mark = self._mark
        return new_value

    @staticmethod
    def _obj_name(value):
        #make sure the actual name is at the end, suitable so we
        #can put .member after it.
        if isinstance(value, type):
            obj_name = "type object %s" % repr(value.__name__)
        elif isinstance(value, types.FunctionType):
            subname = getattr(value, "__name__", value.__class__.__name__)
            obj_name = "function %s" % repr(subname)
        else:
            obj_name = "object %s" % repr(value.__class__.__name__)
        return obj_name

    @staticmethod
    def _lock_name(lock):
        return repr(str(lock))


    @staticmethod
    def _lock_dup_kill(lock_sequence):
        duplicates=set()
        new_sequence=[]
        for lock in lock_sequence:
            if lock not in duplicates:
                new_sequence.append(lock)
                duplicates.add(lock)
        return new_sequence

    @staticmethod
    def _fail_locks_repr(fail_locks):
        lock_names=[]
        for lock in fail_locks:
            lock_names.append(_lock_name(lock))

        return "[" + ", ".join(lock_names) + "]"

    @classmethod
    def _check_lock(cls, lock, **kwargs):
        try:
            valid = lock.permitted(**kwargs)

        except (SecurityError, AttributeError):
            raise
        except Exception as e:
            try:
                error_string = "Lock %s threw non-security exception:" \
                            + " %s" % (_lock_name(lock), str(e))
            except Exception as e:
                error_string = "Unprintable lock threw non-security " \
                             + "exception"

            raise SecurityAttrError(error_string,
                                    fail_locks = [lock],
                                    attr_args = kwargs,
                                    fault = True)

        if isinstance(valid, bool):
            if not valid:
                return (False, [lock])
            else:
                return (True, [])
        else: #permitted CAN return a new list of locks.
            try:
                if valid is None:
                    raise TypeError("None returned") #caught by outside block.

                new_lock_list = locks.sanitize_lock_parameter(valid)
            except Exception as e:
                try:
                    error_string = "Lock %s" % cls._lock_name(lock) \
                                 + ".permitted() returned invalid value: " \
                                 + "%s" % valid

                except Exception as e:
                    error_string = \
                        "Unprintable lock returned invalid value"

                raise SecurityAttrError(error_string,
                                        fail_locks = [lock],
                                        attr_args = kwargs,
                                        fault = True)

            (valid, fail_locks) = \
                cls._check_lock_list(new_lock_list, **kwargs)

            return (valid, fail_locks)

    @classmethod
    def _check_lock_list_item(cls, list_item,
                              list_item_parent = None, **kwargs):
        try:
            list_item = \
                locks.sanitize_lock_list_item(list_item,
                                              parent = list_item_parent)
        except TypeError as e:
            raise SecurityAttrError(str(e),
                                    fail_locks = [],
                                    attr_args = kwargs,
                                    fault = True)
        except Exception as e:
            error_string="Unprintable list item found in lock_list"
            raise SecurityAttrError(error_string,
                                    fail_locks = [],
                                    attr_args = kwargs,
                                    fault = True)


        #Both of the methods below return (valid, fail_locks) tuple
        if isinstance(list_item, locks.Lock):
            return cls._check_lock(list_item, **kwargs)
        else:
            return cls._check_lock_list(list_item, **kwargs)

    @classmethod
    def _check_lock_list_and(cls, lock_list, **kwargs):
        for list_item in lock_list:
            (valid, fail_locks) = \
                cls._check_lock_list_item(list_item,
                                          list_item_parent = lock_list,
                                          **kwargs)
            if not valid:
                return (valid, fail_locks)

        #okay made it through the list.
        return (True, [])

    @classmethod
    def _check_lock_list_or(cls, lock_list, **kwargs):
        all_fail_locks = []
        for list_item in lock_list:
            (valid, fail_locks) = \
                cls._check_lock_list_item(list_item,
                                          list_item_parent = lock_list,
                                          **kwargs)
            if valid:
                return (True, [])
            else:
                all_fail_locks += fail_locks
        return (False, all_fail_locks)

    @classmethod
    def _check_lock_list(cls, lock_list, **kwargs):
        if isinstance(lock_list, locks.LockListOr):
            return cls._check_lock_list_or(lock_list, **kwargs)
        else:
            return cls._check_lock_list_and(lock_list, **kwargs)

    @classmethod
    def _handle_lock_error(cls, valid, fail_locks,
                           obj, name, form, attr_args):
        if valid:
            return
        try:
            fail_locks = cls._lock_dup_kill(fail_locks)
            if len(fail_locks) == 0:
                error_string = "'%s' is a %s-" % (name, form) \
                             + "protected attribute of " \
                             + "%s" % cls._obj_name(obj)

            elif len(fail_locks) == 1:
                lock_name = cls._lock_name(fail_locks[0])
                o_name = cls._obj_name(obj)
                error_string = "Cannot unlock lock %s " % lock_name \
                             + "to %s %s.%s" % (form, o_name, name)

            else:
                fail_lock_str = cls._fail_locks_repr(fail_locks)
                o_name = cls._obj_name(obj)
                error_string = "Cannot unlock any of these locks: " \
                             + "%s to %s %s.%s" % (fail_locks_str,
                                                   form,
                                                   o_name,
                                                   name)

        except SecurityError:
            raise
        except Exception as e:
            error_string = "There were lock(s) that wouldn't open, " \
                         + "but str() on lock(s) or object fails"
            raise SecurityAttrError(error_string,
                                    fail_locks = fail_locks,
                                    attr_args = attr_args,
                                    fault = True)

        raise SecurityAttrError(error_string,
                                fail_locks = fail_locks,
                                attr_args = attr_args)


    @classmethod
    def _attr_lock_check(cls, obj, name, form = "get",
                         attr_locks = [], extra_info = {}):

        wildcard = False
        keyword_args = { "access" : form + "attr",
                         "instance" : obj,
                         "attribute" : name,
                         "wildcard" : None }

        keyword_args.update( extra_info )
        blocked = set(["_rpyc__unwrapped__"])

        #__rpyc_unwrapped__ current blocked.
        if name in blocked:
            raise SecurityAttrError("Magic Attribute Blocked: "
                                  + "%s" % repr(name),
                                    fail_locks = [],
                                    attr_args = keyword_args,
                                    fault = True)


        all_fail_locks = []
        if name in attr_locks:
            keyword_args['wildcard'] = None
            locks = attr_locks[name]
        else:
            if "*" in attr_locks:
                keyword_args['wildcard'] = "*"
                locks = attr_locks["*"]
            else:
                locks = None

        if locks is None:
            valid = False
            fail_locks = []
        else:
            (valid, fail_locks) = \
                cls._check_lock_list(locks,
                                     **keyword_args)
        if valid:
            #Check the "&" wildcard.
            if "&" in attr_locks:
                keyword_args['wildcard'] = "&"
                locks = attr_locks["&"]
                (valid, fail_locks) = \
                    cls._check_lock_list(locks,
                                         **keyword_args)
            if valid:
                return

        #fall through to checking or wildcard
        all_fail_locks += fail_locks
        if "|" in attr_locks:
            keyword_args['wildcard'] = "|"
            locks = attr_locks["|"]
            (valid, fail_locks) = \
                cls._check_lock_list(locks,
                                     **keyword_args)

        if not valid:
            all_fail_locks += fail_locks
            cls._handle_lock_error(valid,
                                   all_fail_locks,
                                   obj, name, form,
                                   keyword_args)

    def getattr_check(self, obj, name):
        self._attr_lock_check(obj, name, form = "get",
                             attr_locks = self.getattr_locks)

    def setattr_check(self, obj, name, value):
        self._attr_lock_check(obj, name, form = "set",
                              attr_locks = self.setattr_locks,
                              extra_info = {"value":value})

    def delattr_check(self, obj, name):
        self._attr_lock_check(obj, name, form = "del",
                              attr_locks = self.delattr_locks)

    def cls_getattr_check(self, cls, name):
        self._attr_lock_check(cls, name, form = "get",
                              attr_locks = self.cls_getattr_locks)

    def cls_setattr_check(self, cls, name, value):
        self._attr_lock_check(cls, name, form = "set",
                              attr_locks = self.cls_setattr_locks,
                              extra_info = {"value":value})

    def cls_delattr_check(self, cls, name):
        self._attr_lock_check(cls, name, form = "del",
                              attr_locks = self.cls_delattr_locks)

    @property
    def lock_local(self):
        return self._lock_local

    @lock_local.setter
    def lock_local(self, value):
        self._lock_local = bool(value)

    @property
    def mark(self):
        """The :attr:`mark` property can be set to ``True`` or
        ``False`` in order to turn on/off "RPyC exposed"
        marking of instances when :func:`repr` is
        called.
        """
        return self._mark

    @mark.setter
    def mark(self, value):
        self._mark = bool(value)

    def dump(self):
        """This dumps a multiple line formatted string
        representation of :class:`OLP` state.
        """
        value = "\n{\n" \
              + " 'getattr_locks':\n%s" % str(self.getattr_locks) \
              + " 'setattr_locks':\n%s" % str(self.setattr_locks) \
              + " 'delattr_locks':\n%s" % str(self.delattr_locks) \
              + " 'cls_getattr_locks':\n%s" % str(self.cls_getattr_locks) \
              + " 'cls_setattr_locks':\n%s" % str(self.cls_setattr_locks) \
              + " 'cls_delattr_locks':\n%s" % str(self.cls_delattr_locks) \
              + "}\n"
        return value

