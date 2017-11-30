"""
Exposer class used for high level exposing objects for RPYC
"""

import functools
import inspect
import types

from rpyc.lib.compat import is_py3k
from rpyc.security.restrictor import SecurityRestrictor, \
    security_restrict, is_restricted

from rpyc.security import locks
from rpyc.security import lock_profiles
from rpyc.security.lock_profiles import MERGE_REPLACE, MERGE_OR, MERGE_AND
from rpyc.security import defaults
from rpyc.security import exceptions
from rpyc.lib.colls import WeakIdMap

#Exposure types.
EXPOSE_DEFAULT = 0
EXPOSE_INSTANCE_GET = 1
EXPOSE_INSTANCE = EXPOSE_INSTANCE_GET
EXPOSE_INSTANCE_SET = 2
EXPOSE_INSTANCE_DEL = 4
EXPOSE_CLASS_GET = 16
EXPOSE_CLASS = EXPOSE_CLASS_GET
EXPOSE_CLASS_SET = 32
EXPOSE_CLASS_DEL = 64
EXPOSE_BOTH_GET = EXPOSE_INSTANCE_GET | EXPOSE_CLASS_GET
EXPOSE_BOTH = EXPOSE_BOTH_GET
EXPOSE_ALL_MASK = EXPOSE_INSTANCE_GET | EXPOSE_INSTANCE_SET \
    | EXPOSE_INSTANCE_DEL | EXPOSE_CLASS_GET | EXPOSE_CLASS_SET \
    | EXPOSE_CLASS_DEL

#EXPOSE_BOTH_SET and EXPOSE_BOTH_DEL are
#not defined because usually would not be a good idea.
#the item in question usually resides in the class
#or instance, not both. An item in the instance
#shadows one in the class.

#bonus merge type just for exposure
#all the other ones are defined in lock_profiles
MERGE_WIPE_AND_REPLACE = -1

class Exposer:
    def __init__(self, restrictor=security_restrict,
                 default_profiles=defaults.default_profiles):
        if not isinstance(restrictor, SecurityRestrictor):
            raise ValueError("restrictor must be an instance of "
                           + "SecurityRestrictor")
        self._restrictor = restrictor

        if not isinstance(default_profiles, defaults.Profiles):
            raise ValueError("default_profiles must be an instance of "
                           + "Profiles")
        self._defaults = default_profiles

        #This only holds routines and classes
        #that are exposed, not all attributes.
        self._exposed = WeakIdMap()

    def _set_exposed(self, object, lock_list_and_profile):
        try:
            self._exposed[object]=lock_list_and_profile
        except TypeError as e:
            object_type=repr(object.__class__.__name__)
            raise TypeError("Cannot @expose a %s" % object_type
                          + " with the @expose decorator")

    def _peel(self, value):
        try:
            return value.__func__
        except AttributeError:
            return value

    def _is_exposed(self, value):
        try:
            lookup_id = self._peel(value)._rpyc__unwrapped_id__
            self._exposed.get_by_id(lookup_id)
            return is_restricted(self._peel(value))
        except (KeyError, AttributeError):
            pass
        return False

    def _get_exposed(self, value):
        try:
            lookup_id = self._peel(value)._rpyc__unwrapped_id__
            return self._exposed.get_by_id(lookup_id)
        except (KeyError, AttributeError):
            raise KeyError(value) #Make sure the key is value, not id(value)

    @staticmethod
    def _get_dict_version_first(search_cls, name):
        for base in inspect.getmro(search_cls):
            if name in base.__dict__:
                return base.__dict__[name]
        return getattr(search_cls, name) #Will throw attribute error.

    @staticmethod
    def _get_dict_version_only(search_cls, name):
        for base in inspect.getmro(search_cls):
            if name in base.__dict__:
                return base.__dict__[name]
        raise AttributeError()

    @classmethod
    def is_staticmethod(cls, search_cls, name):
        try:
            value = cls._get_dict_version_first(search_cls, name)
        except AttributeError:
            return False
        return isinstance(value, staticmethod)

    @classmethod
    def is_classmethod(cls, search_cls, name):
        try:
            value = cls._get_dict_version_first(search_cls, name)
        except AttributeError:
            return False
        return isinstance(value, classmethod)

    #Gets the direct value from a class but only if defined
    #there, will throw AttributeError if not defined in
    #class. Also handles python issue #1785.
    #https://bugs.python.org/issue1785
    def _get_direct(self, search_cls, key):
        try:
            #Okay first we get the value:
            value = getattr(search_cls, key)

            if key in search_cls.__dict__:
                #proof enough defined here.
                #does not have to be same value
                #sometimes dict version is descriptor
                return value

            #Do a hail mary to see if defined by metaclass
            #getattribute--This is a class, not an instance
            #so very unlikely case unless doing weird stuff.

            defined_elsewhere = False

            #Now we check to see if any of the base
            #classes have it. If they do, assume it
            #has been defined there, and not reassigned
            for other_class in inspect.getmro(search_cls)[1:]:
                try:
                    other_value = self._get_direct(other_class, key)
                    if id(other_value) == id(value):
                        defined_elsewhere = True
                        break
                except AttributeError:
                    pass

            if not defined_elsewhere:
                return value

        except AttributeError:
            #Handle python bug #1785
            if key in search_cls.__dict__:
                return search_cls.__dict__[key]

        raise AttributeError() #not descriptive, catch this.

    #This is modeled after inspect.getmembers, except massively
    #simpler as we do not recurse into subclasses.
    def _get_direct_members(self, search_cls):
        results = []
        names = type(search_cls).__dir__(search_cls)
        for key in names:
            try:
                value = self._get_direct(search_cls, key)
                results.append((key, value))
            except AttributeError:
                #Item not found.
                pass
        results.sort(key = lambda pair: pair[0])
        return results

    #This is a decorator we can use.
    def decorate(self, *args, lock=None, inherit=None, mark=True):
        wrapped = None
        if len(args) == 1:
            #Is it a lock or an argument?
            temp_obj = args[0]
            if inspect.isclass(temp_obj) or inspect.isroutine(temp_obj) \
                or isinstance(temp_obj, property):
                wrapped = args[0]
            else:
                try:
                    #don't actually keep the result, just sanitize
                    locks.sanitize_lock_parameter(args[0])

                    if lock is None:
                        lock = args[0]
                    else:
                        name_of_class = self.__class__.__name__
                        raise TypeError("%s got multiple " % name_of_class
                                      + "values for argument 'lock'")

                except TypeError as e:
                    #Back to assuming it is something we want wrapped, this
                    #will most trigger an error block later.
                    wrapped = args[0]

        elif len(args) > 1:
            name_of_class = self.__class__.__name__
            raise TypeError("%s can takes only one " % name_of_class
                          + "positional argument")

        lock_list = locks.sanitize_lock_parameter(lock)
        if wrapped is None:
            return functools.partial(self.decorate,
                                     lock = lock_list,
                                     inherit = inherit,
                                     mark = mark)
        if self._is_exposed(wrapped):
            raise ValueError("Using multiple @expose decorators doesn't work")
        if isinstance(wrapped, property):
            raise ValueError("Must use @expose underneath a "
                           + "@property decorator for it to work")

        return_value = \
            self._generic_expose(wrapped,
                                 lock_list = lock_list,
                                 inherit = inherit,
                                 mark = mark)
        return return_value


    def _is_exposed_class(self, cls):
        if not (inspect.isclass(cls) and self._is_exposed(cls)):
            raise ValueError("cls must be an exposed class that has been "
                             "exposed by this Exposer")

    #This exposes one attribute of a class.
    #This has finer grained access than the decorator.
    #This will not make functions callable, you might
    #want to use routine_expose on the function first.
    #Can also be used for wildcard access.
    def field_expose(self, cls, name, lock = None,
                     inherit = None,
                     exposure = EXPOSE_DEFAULT,
                     merge_mode = MERGE_WIPE_AND_REPLACE):

        new_profile = \
            self._new_profile(inherit = inherit, mark = True)
        self._is_exposed_class(cls)
        lock_list = locks.sanitize_lock_parameter(lock)

        exposure_bad = False
        try:
            exposure = int(exposure)
            if (exposure & EXPOSE_ALL_MASK) != exposure:
                raise TypeError()
        except TypeError as e:
            exposure_bad = True
        if exposure_bad:
            raise ValueError("exposure must be valid mask of exposure "
                             "types (IE: EXPOSE_INSTANCE_GET)")

        try:
            name = lock_profiles.sanitize_attr_key(name)
        except ValueError:
            raise ValueError("name argument must be a valid identifier "
                           + "or wildcard")

        cls_lock_list, olp = self._get_exposed(cls)

        member_set = False
        member = None
        routine = False
        overwrite = False
        try:
            member = self._get_dict_version_first(cls, name)
            member_set = True

            #Convenience--so you don't have to expose it yourself.
            #if already defined.
            if inspect.isroutine(member) and not self._is_exposed(member):
                member = self.routine_expose(member, lock = lock_list, inherit=inherit)
                routine = True
                overwrite = True
        except AttributeError:
            pass

        if (inherit != None) and (routine != True):
            raise ValueError("inherit only works for routines in field_expose")

        self._inner_class_expose(cls, name, cls_lock_list, lock_list, olp,
                                 exposure = exposure,
                                 merge_mode = merge_mode,
                                 member = member,
                                 member_set = member_set)
        if overwrite:
            setattr(cls, name, member)

    #Will not remove wildcard access, unless that is name
    #provided..
    def field_unexpose(self, cls, name):
        self._is_exposed_class(cls)
        lock_list, olp = self._get_exposed(cls)
        olp.wipe_name(name)

    def _inner_class_expose(self, cls, name, cls_lock_list, lock_list, olp,
                            exposure = EXPOSE_DEFAULT,
                            merge_mode = MERGE_WIPE_AND_REPLACE,
                            member = None,
                            member_set = False):

        if merge_mode == MERGE_WIPE_AND_REPLACE:
            olp.wipe_name(name)
            merge_mode = MERGE_REPLACE

        class_get={}
        class_set={}
        class_del={}
        inst_get={}
        inst_set={}
        inst_del={}

        if exposure == EXPOSE_DEFAULT:
            if lock_profiles.is_attr_wildcard(name):
                raise ValueError("Cannot use a wildcard name and set "
                               + "exposure to EXPOSURE_DEFAULT")

            try:
                if not member_set:
                    member = getattr(cls, name)
            except AttributeError as e:
                raise ValueError("To use EXPOSE_DEFAULT, %s must " % name
                               + "be defined value for class")

            if self.is_classmethod(cls, name):
                exposure = EXPOSE_BOTH
            elif self.is_staticmethod(cls, name):
                exposure = EXPOSE_BOTH
            else:
                binding_descriptor = False
                try:
                    value = self._get_dict_version_only(cls, name)
                    if hasattr(value, "__get__"):
                        binding_descriptor = True
                except AttributeError:
                    pass

                if binding_descriptor:
                    #Allowing unbound version could cause access problems.
                    #IE: normal instance methods that bind themselves
                    #to the instance on a __get__.
                    #
                    #If we allowed the unbound version to be exposed,
                    #you would have to pass self to them, which would
                    #allow them to be used on another instance entirely.
                    #
                    #That would be asking for trouble, from a security
                    #standpoint
                    exposure = EXPOSE_INSTANCE
                else:
                    exposure = EXPOSE_BOTH

        if (exposure & EXPOSE_INSTANCE_GET) != 0:
            inst_get[name] = locks.LL_And([cls_lock_list,
                                           lock_list])
        if (exposure & EXPOSE_INSTANCE_SET) != 0:
            inst_set[name] = locks.LL_And([cls_lock_list,
                                           lock_list])
        if (exposure & EXPOSE_INSTANCE_DEL) != 0:
            inst_del[name] = locks.LL_And([cls_lock_list,
                                           lock_list])
        if (exposure & EXPOSE_CLASS_GET) != 0:
            class_get[name] = locks.LL_And([cls_lock_list,
                                            lock_list])
        if (exposure & EXPOSE_CLASS_SET) != 0:
            class_set[name] = locks.LL_And([cls_lock_list,
                                            lock_list])
        if (exposure & EXPOSE_CLASS_DEL) != 0:
            class_del[name] = locks.LL_And([cls_lock_list,
                                            lock_list])
        olp.merge_specified(merge_mode,
                            getattr_locks=inst_get,
                            setattr_locks=inst_set,
                            delattr_locks=inst_del,
                            cls_getattr_locks=class_get,
                            cls_setattr_locks=class_set,
                            cls_delattr_locks=class_del)

    def _new_profile(self, inherit = None, mark = True):
        new_profile = lock_profiles.LockProfile()
        new_profile.mark = mark

        if inherit is not None:
            if isinstance(inherit, lock_profiles.LockProfile):
                new_profile.and_profile(inherit)
            elif inspect.isclass(inherit):
                valid = False
                try:
                    restrictor = self._restrictor
                    default_profile = \
                        restrictor.get_default_profile_for_class(inherit)
                    new_profile.and_profile(default_profile)
                    valid = True
                except KeyError:
                    pass
                if not valid:
                    raise ValueError("Cannot set `inherit` to an unexposed class")
            else:
                raise ValueError("Must set `inherit` to LockProfile or class")
        return new_profile

    def class_expose(self, value, lock = None, inherit=None, mark=True):
        if not inspect.isclass(value):
            raise ValueError("class_expose first parameter isn't a class")
        if self._is_exposed(value):
            raise ValueError("class already exposed")

        new_profile = self._new_profile(inherit = inherit, mark = mark)

        cls_lock_list = locks.sanitize_lock_parameter(lock)

        items=[(key, item) for key, item in self._get_direct_members(value)]
        for key, member in items:
            exposure = EXPOSE_DEFAULT
            #If it is a direct member of new class, WIPE access to it on inherted
            #profile so we don't accidentally access it via shadowed permission.
            new_profile.wipe_name(key)

            #Deal with properties
            #We only allow property access on instance, not on class.
            if isinstance(member, property):
                dict_setup = {"fget":EXPOSE_INSTANCE_GET,
                              "fset":EXPOSE_INSTANCE_SET,
                              "fdel":EXPOSE_INSTANCE_DEL}

                for sub_key in dict_setup:
                    sub_member = getattr(member, sub_key)
                    if (sub_member != None) and self._is_exposed(sub_member):
                        lock_list, old_profile = self._get_exposed(sub_member)

                        sub_exposure=dict_setup[sub_key]
                        self._inner_class_expose(value, key,
                                                 cls_lock_list,
                                                 lock_list,
                                                 new_profile,
                                                 exposure = sub_exposure,
                                                 merge_mode = MERGE_REPLACE)

            elif self._is_exposed(member):
                lock_list, old_profile = self._get_exposed(member)
                dict_member = self._get_dict_version_first(value, key)

                if self.is_routine_descriptor(dict_member):
                    if not is_restricted(dict_member):
                        member = \
                            self.routine_descriptor_expose(dict_member,
                                                          lock = lock_list)
                        #Restore new member
                        setattr(value, key, member)

                self._inner_class_expose(value, key,
                                         cls_lock_list,
                                         lock_list,
                                         new_profile,
                                         exposure = exposure,
                                         member = member,
                                         member_set = True)

        #Merge with default profile.
        defaults = self._defaults
        class_lock_profile = \
            defaults.create_class_olp(value,
                                      lock = cls_lock_list)

        new_profile.and_profile(class_lock_profile)
        security_wrapped_class=self._restrictor(value,
                                                new_profile,
                                                default=True)

        self._set_exposed(value, (cls_lock_list, new_profile))
        self._set_exposed(security_wrapped_class,
                         (cls_lock_list, new_profile))
        return security_wrapped_class


    @classmethod
    def is_routine_descriptor(cls, value):
        if not inspect.isroutine(value):
            return False
        if hasattr(value, "__func__") and hasattr(value, "__get__"):
            return True
        return False

    @classmethod
    def _get_routine_self(cls, value):
        if is_py3k:
            im_self='__self__'
        else:
            im_self='im_self'
        return getattr(value, im_self)

    @classmethod
    def _routine_descriptor_remake(cls, original, function):
        #No way to change descriptor, can only make new one.
        #If there is a __self__, is two parameter call
        try:
            im_self = cls._get_routine_self(original)
            new_descriptor = original.__class__(function, im_self)
        except AttributeError:
            #otherwise, one parameter.
            new_descriptor = original.__class__(function)
        return new_descriptor

    def routine_descriptor_expose(self, value, lock = None):
        if not self.is_routine_descriptor(value):
            raise ValueError("value must be a routine descriptor (IE: classmethod)")

        lock_list = locks.sanitize_lock_parameter(lock)

        descriptor_profile = self._new_profile()

        defaults = self._defaults
        restrictor = self._restrictor

        call_descriptor_profile = \
            defaults.create_routine_descriptor_olp(value,
                                                   lock = lock_list)

        descriptor_profile.and_profile(call_descriptor_profile)

        restricted_descriptor = restrictor(value,
                                           descriptor_profile,
                                           default = False)
        #Cannot expose weak refs to the base types, so we do the
        #best we can.
        self._set_exposed(restricted_descriptor, (lock_list, descriptor_profile))
        return restricted_descriptor

    def routine_expose(self, value, lock = None, inherit = None):
        new_function_profile = \
            self._new_profile(inherit = inherit, mark = True)

        #Weird reversed order of these is because functions
        #are one of the objects that can't be subclassed,
        #and therefore isinstance() won't work properly.
        #therefore, the exposed version doesn't even register
        #as a routine to inspect.isroutine
        if self._is_exposed(value):
            raise ValueError("value already exposed")
        if not inspect.isroutine(value):
            raise ValueError("routine_expose first parameter isn't routine")

        lock_list = locks.sanitize_lock_parameter(lock)

        #We do not expose anything that might return an object
        #that is at all changeable.
        #
        #'__defaults__' is out for example, because the objects
        #inside it can be mutable.

        restrictor = self._restrictor
        defaults = self._defaults

        if self.is_routine_descriptor(value):
            routine_descriptor = True
            function = value.__func__
        else:
            routine_descriptor = False
            function = value

        #Now restrict the function.
        call_lock_profile = \
            defaults.create_routine_olp(value,
                                        lock = lock_list)

        new_function_profile.and_profile(call_lock_profile)
        #This is a routine, if I set default=True this will apply
        #to everything of same type. Do not do that.
        new_function = restrictor(function,
                                  new_function_profile,
                                  default = False)
        self._set_exposed(function, (lock_list, new_function_profile))
        self._set_exposed(new_function, (lock_list, new_function_profile))
        return_value = new_function

        #@classmethod/@staticmethod/@abstractmethod
        if routine_descriptor:
            #No way to change descriptor, can only make new one.
            new_descriptor = \
                self._routine_descriptor_remake(value, new_function)
            return_value = \
                self.routine_descriptor_expose(new_descriptor,
                                               lock = lock_list)

        return return_value

    def _generic_expose(self, value, lock_list = None,
                        inherit=None, mark=True):
        if inspect.isclass(value):
            return self.class_expose(value, lock = lock_list,
                                     inherit = inherit, mark = mark)
        elif inspect.isroutine(value):
            return self.routine_expose(value, lock = lock_list,
                                       inherit = inherit)
        else:
            raise TypeError("Unable to expose %s " % repr(value)
                          + "of type %s" % (repr(type(value))) )

    #Defines expose/class_expose/routine_expose/field_expose
    #in the current module based on this instance of Exposer
    #
    #Defined to allow use of multple Exposers (not
    #a common thing)
    def define_shortcuts(self):
        global expose
        global class_expose
        global routine_expose
        global routine_descriptor_expose
        global field_expose
        global field_unexpose

        expose = default_exposer.decorate
        class_expose = default_exposer.class_expose
        routine_expose = default_exposer.routine_expose
        routine_descriptor_expose = default_exposer.routine_descriptor_expose
        field_expose = default_exposer.field_expose
        field_unexpose = default_exposer.field_unexpose

#define default.
default_exposer = Exposer()
default_exposer.define_shortcuts()

