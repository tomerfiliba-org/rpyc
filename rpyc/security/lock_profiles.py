"""
Definition of a an object LockProfile (olp)
"""

import types

from rpyc.lib.compat import is_py3k
from rpyc.lib.colls import MapTypeDict
from rpyc.security import locks
from rpyc.security.exceptions import SecurityError, SecurityAttrError

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
        if value in keyword.kwlist:
            return valse
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
    def _map_key(self, key):
        key = sanitize_attr_key(key)
        return key

    def _map_item(self, item):
        if isinstance(item, locks.Lock):
            item=[item]
        item = locks.sanitize_and_copy_lock_list(item)
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
class LockProfile(object):
    """Placeholder"""
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

        self._wipe_attr_locks(self.getattr_locks, getattr_locks)
        self._wipe_attr_locks(self.setattr_locks, setattr_locks)
        self._wipe_attr_locks(self.delattr_locks, delattr_locks)
        self._wipe_attr_locks(self.cls_getattr_locks, cls_getattr_locks)
        self._wipe_attr_locks(self.cls_setattr_locks, cls_setattr_locks)
        self._wipe_attr_locks(self.cls_delattr_locks, cls_delattr_locks)

    #Makes nothing readable, but no locks included
    def wipe_name(self, name):
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
        self.merge_specified(merge_mode = MERGE_REPLACE,
                             **kwargs)

    def and_specified(self, **kwargs):
        self.merge_specified(merge_mode = MERGE_AND,
                             **kwargs)

    def or_specified(self, **kwargs):
        self.merge_specified(merge_mode = MERGE_OR,
                            **kwargs)

    def and_profile(self, other):
        self.and_specified(getattr_locks = other.getattr_locks,
                           setattr_locks = other.setattr_locks,
                           delattr_locks = other.delattr_locks,
                           cls_getattr_locks = other.getattr_locks,
                           cls_setattr_locks = other.cls_setattr_locks,
                           cls_delattr_locks = other.cls_delattr_locks)

    def or_profile(self, other):
        self.and_specified(getattr_locks = other.getattr_locks,
                           setattr_locks = other.setattr_locks,
                           delattr_locks = other.delattr_locks,
                           cls_getattr_locks = other.getattr_locks,
                           cls_setattr_locks = other.cls_setattr_locks,
                           cls_delattr_locks = other.cls_delattr_locks)

    def total_expose(self, lock_list=[], wildcard="|"):
        lock_list = locks.sanitize_and_copy_lock_list(lock_list)

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

    def read_expose(self, lock_list=[], wildcard="|"):
        lock_list = locks.sanitize_and_copy_lock_list(locks_list)

        if not wildcard in "*&|":
            raise ValueError("wildcard must be '*', '&', or '|'")

        getattr_locks = {wildcard:lock_list}
        cls_getattr_locks = {wildcard:lock_list}

        self.replace_specified(getattr_locks = getattr_locks,
                               cls_getattr_locks = cls_getattr_locks)


    def push(self):   #Stores copy of self on stack to pop to.
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
        if self._push is None:
            raise SecurityError("LockProfile stack underflow--too many LockProfile.pop calls")
        self.copy_into(self, self._push, include_stack = True)

    def copy_into(self, other, include_stack = False):
        self.getattr_locks = LAD(other.getattr_locks)
        self.setattr_locks = LAD(other.setattr_locks)
        self.delattr_locks = LAD(other.delattr_locks)
        self.cls_getattr_locks = LAD(other.cls_getattr_locks)
        self.cls_setattr_locks = LAD(other.cls_setattr_locks)
        self.cls_delattr_locks = LAD(other.cls_delattr_locks)
        self._lock_local = other._lock_local
        self._mark = other._mark

        if include_stack:
            self._push = other._push
        else:
            self._push = None

    def copy(self, include_stack = False):
        new_value = self.__class__()
        new_value.copy_into( self, include_stack = include_stack )

        return new_value

    def read_only_copy(self):
        """Placeholder"""
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
                new_lock_list = locks.sanitize_and_copy_lock_list(valid)
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
            return cls._check_lock(list_item)
        else:
            return cls._check_lock_list(list_item)

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
        blocked = {"__s_unwrapped_type__",
                   "__s_restricted__"}

        #A few things are blocked out of hand, if they made it this far:
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
        return self._mark

    @mark.setter
    def mark(self, value):
        self._mark = bool(value)

    def dump(self):
        value = "\n{\n" \
              + " 'getattr_locks':\n%s" % str(self.getattr_locks) \
              + " 'setattr_locks':\n%s" % str(self.setattr_locks) \
              + " 'delattr_locks':\n%s" % str(self.delattr_locks) \
              + " 'cls_getattr_locks':\n%s" % str(self.cls_getattr_locks) \
              + " 'cls_setattr_locks':\n%s" % str(self.cls_setattr_locks) \
              + " 'cls_delattr_locks':\n%s" % str(self.cls_delattr_locks) \
              + "}\n"
        return value

