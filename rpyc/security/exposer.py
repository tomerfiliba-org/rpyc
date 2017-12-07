"""
The :mod:`rpyc.security.exposer` module is used to do high level exposure
of classes as `RPyC Exposed`

This is chiefly accomplished via methods of the class :class:`Exposer`.

Module Level Functions
----------------------

Most users will not have any need to use more than one instance of
:class:`Exposer`. For that reason, an instance is
already instantiated as
:data:`rpyc.security.exposer.default_exposer`. Many of the methods
of this instance are also accessable as module level functions for
convenience:

.. decorator:: expose

    This is actually :meth:`@Exposer.expose <Exposer.expose>` of
    :data:`rpyc.security.exposer.default_exposer`

.. function:: class_expose

    This is :meth:`Exposer.class_expose` of
    :data:`rpyc.security.exposer.default_exposer`

.. function:: field_expose

    This is :meth:`Exposer.field_expose` of
    :data:`rpyc.security.exposer.default_exposer`

.. function:: field_unexpose

    This is :meth:`Exposer.field_unexpose` of
    :data:`rpyc.security.exposer.default_exposer`

.. function:: routine_expose

    This is :meth:`Exposer.routine_expose` of
    :data:`rpyc.security.exposer.default_exposer`

.. function:: routine_descriptor_expose

    This is :meth:`Exposer.routine_descriptor_expose` of
    :data:`rpyc.security.exposer.default_exposer`

Exposer Class
-------------

"""

import functools
import inspect
import types

from rpyc.lib.compat import is_py3k
from rpyc.security.restrictor import SecurityRestrictor, \
    security_restrict
from rpyc.security.utility import is_exposed

from rpyc.security import locks
from rpyc.security import olps
from rpyc.security.olps import MERGE_REPLACE, MERGE_OR, MERGE_AND
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
#all the other ones are defined in olps
MERGE_WIPE_AND_REPLACE = -1

class Exposer:
    """This is a class that implements a high level api to create
    `RPyC Exposed` objects.

    In most use cases there will be only one instance of this
    class.  In this case, use
    :data:`rpyc.security.exposer.default_exposer` which is a
    pre-instantiated version of this class.

    Many of the methods of that instance can also
    be accessed as functions of the :mod:`rpyc.security.exposer`
    module.

    .. decoratormethod:: expose
                         expose(lock=None, inherit=None, mark=True)

        This is a decorator that can be used to expose functions, classes,
        methods, static methods, class methods, and properties as
        `RPyC Exposed` objects. For other forms of data, use
        :meth:`field_expose`. You do not have to specify
        any arguments for the decorator. `@expose` will use
        the default arguments.

        :param lock: This can be a single :class:`Lock <rpyc.security.locks.Lock>`,
            or a :class:`LockListShared <rpyc.security.locks.LockListShared>`
        :param inherit: Argument can be an :class:`OLP` or `RPyC Exposed`
            class (which will effectively act the same as passing in
            :func:`get_olp(inherit) <rpyc.security.utils.get_olp>`)
        :param bool mark: Whether instances of this object should
            be marked as `RPyC exposed` when :func:`repr` is called
            on them.

        If `lock` is ``None``, no locks are applied. You can also pass in any
        iterable, and it will be treated as if you passed in a
        :class:`LockListAnd <rpyc.security.locks.LockListAnd>`
        of those elements.

        If `inherit` is ``None`` nothing is inherited.

        .. note ::

            `inherit` is usually only used when exposing classes.
            Use it on methods and routines only if you want
            to inherit an :class:`OLP` that specifically
            configures access to the attributes of a
            routine object of the type being exposed.

        The :class:`OLP <rpyc.security.olps.OLP>` is
        created for the target using the following steps:

            * A blank :class:`OLP` is created, configured with `mark`.
            * :meth:`and_olp <rpyc.security.olps.OLP.and_olp>`
              is used with the new :class:`OLP` and the `inherit`
              :class:`OLP` (if any) to update the new :class:`OLP`.
            * A default `OLP` is created via the
              :class:`Profiles <rpyc.security.defaults.Profiles>`
              instance set for :class:`Exposer`, based on what type the target
              is.
              :meth:`and_olp <rpyc.security.olps.OLP.and_olp>`
              is used to merge these defaults into the :class:`OLP` being
              constructed.
            * If the target is a class, any new (non-inherited)
              members of the class are scanned to see if they themselves
              were exposed using the :class:Exposer. If they are, access to
              them is added to the newly generated :class:`OLP` by name,
              using the `lock` parameter provided (if any).

        Access to members of the class is as follows (using `lock`):

            * :meth:`_rpyc_getattr` access is added for
              class and  static methods. This access is
              added both for instances and the class
              itself.
            * :meth:`_rpyc_getattr` access is added for
              regular methods. Access is only added for
              instances.
            * For properties access via :meth:`_rpyc_getattr`,
              :meth:`_rpyc_setattr`, and
              :meth:`_rpyc_delattr` are added, but only
              if each of their respective getter, setter, and
              deleter methods have been exposed. Access is only
              added for instances.

    """
    def __init__(self, restrictor=security_restrict,
                 default_profiles=defaults.default_profiles):
        if not isinstance(restrictor, SecurityRestrictor):
            raise TypeError("restrictor must be an instance of "
                           + "SecurityRestrictor")
        self._restrictor = restrictor

        if not isinstance(default_profiles, defaults.Profiles):
            raise TypeError("default_profiles must be an instance of "
                           + "Profiles")
        self._defaults = default_profiles

        #This only holds routines and classes
        #that are exposed, not all attributes.
        self._exposed = WeakIdMap()

    def _set_exposed(self, object, lock_list_and_olp):
        try:
            self._exposed[object]=lock_list_and_olp
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

            #this test if exposed by SecurityRestrictor--different
            #than exposed by Exposer.
            return is_exposed(self._peel(value))
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
        names = dir(search_cls)
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
    def expose(self, *args, **kwargs):
        for key in kwargs:
            if key not in ["lock", "inherit", "mark"]:
                raise TypeError("expose() got unexpected keyword argument %s" % repr(key))

        lock = kwargs.get("lock", None)
        inherit = kwargs.get("inherit", None)
        mark = kwargs.get("mark", True)

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
            return functools.partial(self.expose,
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

    def class_expose(self, value, lock = None, inherit=None, mark=True):
        """This can be used to expose a class that hasn't been exposed
        using the @expose decorator

        :param value: Class to expose
        :param lock: This can be a single :class:`Lock <rpyc.security.locks.Lock>`,
            or a :class:`LockListShared <rpyc.security.locks.LockListShared>`
        :param inherit: Argument can be an :class:`OLP` or `RPyC Exposed`
            class (which will effectively act the same as passing in
            :func:`get_olp(inherit) <rpyc.security.utils.get_olp>`)
        :param bool mark: Whether instances of this object should
            be marked as `RPyC exposed` when :func:`repr` is called
            on them.
        :return: A `RPyC Exposed` version of the class that can be used.

        If `lock` is ``None``, no locks are applied. You can also pass in any
        iterable, and it will be treated as if you passed in a
        :class:`LockListAnd <rpyc.security.locks.LockListAnd>`
        of those elements.

        if `inherit` is ``None`` nothing is inherited.

        This operates the same as the
        :meth:rpyc.exposer.Exposer.@expose decorator does on a class.
        """
        if not inspect.isclass(value):
            raise TypeError("class_expose first parameter isn't a class")
        if self._is_exposed(value):
            raise ValueError("class already exposed")

        new_olp = self._new_olp(inherit = inherit, mark = mark)

        cls_lock_list = locks.sanitize_lock_parameter(lock)

        items=[(key, item) for key, item in self._get_direct_members(value)]

        for key, member in items:
            exposure = EXPOSE_DEFAULT
            #If it is a direct member of new class, WIPE access to it on inherted
            #OLP so we don't accidentally access it via shadowed permission.
            new_olp.wipe_name(key)

            #Deal with properties
            #We only allow property access on instance, not on class.
            if isinstance(member, property):
                dict_setup = {"fget":EXPOSE_INSTANCE_GET,
                              "fset":EXPOSE_INSTANCE_SET,
                              "fdel":EXPOSE_INSTANCE_DEL}

                for sub_key in dict_setup:
                    sub_member = getattr(member, sub_key)
                    if (sub_member != None) and self._is_exposed(sub_member):
                        lock_list, old_olp = self._get_exposed(sub_member)

                        sub_exposure=dict_setup[sub_key]
                        self._inner_class_expose(value, key,
                                                 cls_lock_list,
                                                 lock_list,
                                                 new_olp,
                                                 exposure = sub_exposure,
                                                 merge_mode = MERGE_REPLACE)

            elif self._is_exposed(member):
                lock_list, old_olp = self._get_exposed(member)
                dict_member = self._get_dict_version_first(value, key)

                if self.is_routine_descriptor(dict_member):
                    #We only check is_exposed rather than
                    #self._is_exposed here, because some
                    #desciptors can't be weak ref'd.
                    if not is_exposed(dict_member):
                        member = \
                            self.routine_descriptor_expose(dict_member,
                                                          lock = lock_list)
                        #Restore new member
                        setattr(value, key, member)

                self._inner_class_expose(value, key,
                                         cls_lock_list,
                                         lock_list,
                                         new_olp,
                                         exposure = exposure,
                                         member = member,
                                         member_set = True)

        #Merge with default olp.
        defaults = self._defaults
        class_olp = \
            defaults.create_class_olp(value,
                                      lock = cls_lock_list)

        new_olp.and_olp(class_olp)
        security_wrapped_class=self._restrictor(value,
                                                new_olp,
                                                default=True)

        self._set_exposed(value, (cls_lock_list, new_olp))
        self._set_exposed(security_wrapped_class,
                         (cls_lock_list, new_olp))
        return security_wrapped_class




    #This exposes one attribute of a class.
    #This has finer grained access than the decorator.
    #Can also be used for wildcard access.
    def field_expose(self, cls, name, lock = None,
                     inherit = None,
                     exposure = EXPOSE_DEFAULT,
                     merge_mode = MERGE_WIPE_AND_REPLACE):
        #Sphinx replaces constants with actual values, so use first line of doc to override that.
        """field_expose(cls, name, lock=None, inherit=None, exposure=EXPOSE_DEFAULT, merge_mode=MERGE_WIPE_AND_REPLACE)

        This can be used to explicitly expose fields and/or
        methods after a class has been exposed.

        :param cls: Class the field is in
        :param (str) name: Name of the field
        :param lock: This can be a single :class:`Lock <rpyc.security.locks.Lock>`,
            or a :class:`LockListShared <rpyc.security.locks.LockListShared>`
        :param inherit: Argument can be an :class:`OLP` or `RPyC Exposed`
            class (which will effectively act the same as passing in
            :func:`get_olp(inherit) <rpyc.security.utils.get_olp>`)
        :param exposure: Bit field that specifies how the field can be
             exposed.
        :param merge_mode: Specifies how the new :class:`OLP` settings for
            name` are merged with existing :class:`OLP` settings for `name`
            (if present).

        `name` is usually a field name, but it can also be
        set to a
        :class:`OLP <rpyc.security.olps.OLP>`
        wildcard, to modify wildcard :class:`OLP` settings.

        `exposure` is a bit field:

            * :data:`EXPOSE_DEFAULT` = 0
                Do default exposure based on what `name` is inside
                `cls`. To use this option, `name` must exist in the
                class and not be a wildcard.

                Methods, class methods,
                and static methods are exposed the same was if
                they were hit with the @expose decorator.

                Data elements must already exist at the class level
                for EXPOSE_DEFAULT to work, so they are given
                :meth:`_rpyc_getattr` access for both classes and
                istances.
                That is unless, they implement :meth:`__get__`, in which
                case they are considered descriptors and
                :meth:`_rpyc_getattr` access is only added for
                any instances (not on the class itself).

            * :data:`EXPOSE_INSTANCE_GET` = 1
                If this bit is set, :meth:`_rpyc_getattr` access is set up
                to `name`
                on instances of `cls`
                using the `lock` parameter provided.

            * :data:`EXPOSE_INSTANCE_SET` = 2
                If this bit is set, :meth:`_rpyc_setattr` access is set up
                to `name`
                on instances of `cls`
                using the `lock` parameter provided.

            * :data:`EXPOSE_INSTANCE_DEL` = 4
                If this bit is set, :meth:`_rpyc_delattr` access is set up
                to `name`
                on instances of `cls`
                using the `lock` parameter provided.

            * :data:`EXPOSE_CLASS_GET` = 16
                If this bit is set, :meth:`_rpyc_getattr` access is set up
                to `name`
                on `cls` itself
                using the `lock` parameter provided.

             * :data:`EXPOSE_CLASS_SET` = 32
                If this bit is set, :meth:`_rpyc_setattr` access is set up
                to `name`
                on `cls` itself
                using the `lock` parameter provided.

            * :data:`EXPOSE_CLASS_DEL` = 64
                If this bit is set, :meth:`_rpyc_delattr` access is set up
                to `name`
                on `cls` itself
                using the `lock` parameter provided.

            * :data:`EXPOSE_INSTANCE` is shorthand for :data:`EXPOSE_INSTANCE_GET`

            * :data:`EXPOSE_CLASS` is shorthand for :data:`EXPOSE_CLASS_GET`

            * :data:`EXPOSE_BOTH_GET` is shorthand for:
                :data:`EXPOSE_INSTANCE_GET` | :data:`EXPOSE_CLASS_GET`

            * :Data:`EXPOSE_BOTH` is shorthand for :data:`EXPOSE_BOTH_GET`

        `merge_mode` is as specified for
        :meth:`olp.merge_specified <rpyc.security.olps.OLP.merge_specified>`.
        The parameters ```getattr_locks``. ``setattr_locks``,
        ``delattr_locks``, ``cls_getattr_locks``, ``cls_setattr_locks``,
        and ``cls_delattr_locks`` will all be set to  ``None`` for the
        underlying call to :meth:`olp.merge_specified` unless they are
        explicitly being changed given the setting of `exposure`.

        Additionally, you can use :data:`MERGE_WIPE_AND_REPLACE` defined in :mod:`rpyc.security.exposer`
        for this function, which means all data in the :class:`OLP` for `name` will be wiped
        prior to doing a :data:`MERGE_REPLACE`, via
        :meth:`olp.wipe_name() <rpyc.security.olps.OLP.wipe_name>`.

        .. note ::
            Exposing existing methods via :meth:`field_expose()` will
            automatically expose those routines via
            :meth:`routine_expose(cls.name, lock = lock, inherit = inherit) <routine_expose>`
            for convenience. If you use :meth:`field_expose` to expose a
            routine that doesn't exist yet, and later want to add the routine
            to a class or instance, use :meth:`routine_expose` to
            make a `RPyC exposed` version of the routine to add.

            An un-exposed method may otherwise not be callable
            (depending on protocol settings). This is because
            ``_rpyc_getattr("__call__")`` will not work.
        """

        new_olp = \
            self._new_olp(inherit = inherit, mark = True)
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
            name = olps.sanitize_attr_key(name)
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
        """This can be used to remove an exposed
        field or method from an existing `RPyC Exposed`
        class

        :param cls: Class the field is in
        :param (str) name: Name of the field

        This wipes all references to `name` from the associated
        :class:`OLP`. It can be used with `name` set to an :class:`OLP`
        wildcard if desirable to remove all references to that wildcard
        from the :class:`OLP`
        """

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
            if olps.is_attr_wildcard(name):
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

    def _new_olp(self, inherit = None, mark = True):
        new_olp = olps.OLP()
        new_olp.mark = mark

        if inherit is not None:
            if isinstance(inherit, olps.OLP):
                new_olp.and_olp(inherit)
            elif inspect.isclass(inherit):
                valid = False
                try:
                    restrictor = self._restrictor
                    default_olp = \
                        restrictor.get_default_profile_for_class(inherit)
                    new_olp.and_olp(default_olp)
                    valid = True
                except KeyError:
                    pass
                if not valid:
                    raise ValueError("Cannot set `inherit` to an unexposed class")
            else:
                raise ValueError("Must set `inherit` to OLP or class")
        return new_olp

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

    def routine_expose(self, value, lock = None, inherit = None):
        """This works on both routines and routine descriptors
        to expose a routine. This works identically to how it
        the :meth:`expose` decorator works on routines.

        :param value: Routine to expose
        :param lock: This can be a single :class:`Lock <rpyc.security.locks.Lock>`,
            or a :class:`LockListShared <rpyc.security.locks.LockListShared>`
        :param inherit: Argument can be an :class:`OLP` or `RPyC Exposed`
            class (which will effectively act the same as passing in
            :func:`get_olp(inherit) <rpyc.security.utils.get_olp>`)
        :param bool mark: Whether instances of this object should
            be marked as `RPyC exposed` when :func:`repr` is called
            on them.
        :return: A `RPyC Exposed` version of the routine that can be used.

        If `lock` is ``None``, no locks are applied. You can also pass in any
        iterable, and it will be treated as if you passed in a
        :class:`LockListAnd <rpyc.security.locks.LockListAnd>`
        of those elements.

        if `inherit` is ``None`` nothing is inherited.

        .. note ::
            Since this operates with routines, `inherit` should not
            normally be used (as it is typically used with classes). Use
            `inherit` only if you want to inherit an :class:`OLP` that
            that specifically configures access to the attributes of a
            routine object of the same type as `value`.

        This operates the same as the
        :meth:rpyc.exposer.Exposer.@expose decorator does on a routine
        """

        new_function_olp = \
            self._new_olp(inherit = inherit, mark = True)

        #Weird reversed order of these is because functions
        #are one of the objects that can't be subclassed,
        #and therefore isinstance() won't work properly.
        #therefore, the exposed version doesn't even register
        #as a routine to inspect.isroutine
        if self._is_exposed(value):
            raise ValueError("value already exposed")
        if not inspect.isroutine(value):
            raise TypeError("routine_expose first parameter isn't routine")

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
        call_olp = \
            defaults.create_routine_olp(value,
                                        lock = lock_list)

        new_function_olp.and_olp(call_olp)
        #This is a routine, if I set default=True this will apply
        #to everything of same type. Do not do that.
        new_function = restrictor(function,
                                  new_function_olp,
                                  default = False)
        self._set_exposed(function, (lock_list, new_function_olp))
        self._set_exposed(new_function, (lock_list, new_function_olp))
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

    def routine_descriptor_expose(self, value, lock = None):
        """This works on routine descriptors
        (IE: ``classmethod(func)`` creates a routine descriptor).

        This should rarely be used. It is used to expose
        a routine descriptor without exposing the underlying
        routine.

        :param value: Routine to expose
        :param lock: This can be a single :class:`Lock <rpyc.security.locks.Lock>`,
            or a :class:`LockListShared <rpyc.security.locks.LockListShared>`
        :return: A `RPyC Exposed` version of the routine descriptor

        If `lock` is ``None``, no locks are applied. You can also pass in any
        iterable, and it will be treated as if you passed in a
        :class:`LockListAnd <rpyc.security.locks.LockListAnd>`
        of those elements.

        This would typically be used in rare cases where you have
        an already exposed routine, but need to expose the descriptor
        for it.

        IE::

            def foo(obj):
                return obj.info

            class bar:
                pass

            routine_expose(foo)
            class_expose(bar)

            bar.foo = routine_descriptor_expose(classmethod(foo))

        Nearly the same effect for this example could be
        accomplished more simply::

            def foo(obj):
                return obj.info

            class bar:
                pass

            class_expose(bar)

            bar.foo = routine_expose(classmethod(foo))

        The difference of course would be that the naked ``foo``
        function would not be exposed.
        """

        if not self.is_routine_descriptor(value):
            raise TypeError("value must be a routine descriptor (IE: classmethod)")

        lock_list = locks.sanitize_lock_parameter(lock)

        descriptor_olp = self._new_olp()

        defaults = self._defaults
        restrictor = self._restrictor

        call_descriptor_olp = \
            defaults.create_routine_descriptor_olp(value,
                                                   lock = lock_list)

        descriptor_olp.and_olp(call_descriptor_olp)

        restricted_descriptor = restrictor(value,
                                           descriptor_olp,
                                           default = False)
        #Cannot expose weak refs to the base types, so we do the
        #best we can.
        self._set_exposed(restricted_descriptor, (lock_list, descriptor_olp))
        return restricted_descriptor

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


    @property
    def default_profiles(self):
        """The default profiles property is a
        :class:`rpyc.security.default.Profiles`
        object that can be get/set for the
        :class:`Exposer`. The initial value is
        set by the :class:`Exposer` constructor.

        The current value is used as documented
        in the :meth:`@expose <expose>` when creating
        a :class:`OLP` for
        classes/routines/routine_descriptors/etc.
        """
        return self._defaults

    @default_profiles.setter
    def default_profiles(self, value):
        if not isinstance(value, defaults.Profiles):
            raise TypeError("default_profiles must be an instance of "
                           + "Profiles")
        self._defaults = value

    #Defines expose/class_expose/routine_expose/field_expose
    #in the current module based on this instance of Exposer
    #
    #Defined to allow use of multple Exposers (not
    #a common thing)
    def define_module_functions(self):
        """This exports methods of
        the :class:`Exposer` class to the
        current calling global namespace.

        :func:`expose`, :func:`class_expose`,
        :func:`field_expose`, :func:`field_unexpose`
        :func:`routine_expose`, and
        :func:`routine_descriptor_expose` are all
        created as new functions in the containing
        namespace, and they call the methods of the same
        name on `self`.

        This can be used if you have a need for multiple
        :class:`Exposer` instances, and you wish to swap
        out the convenience functions (or use them
        in a different namespace).
        """

        global expose
        global class_expose
        global field_expose
        global field_unexpose
        global routine_expose
        global routine_descriptor_expose

        expose = default_exposer.expose
        class_expose = default_exposer.class_expose
        field_expose = default_exposer.field_expose
        field_unexpose = default_exposer.field_unexpose
        routine_expose = default_exposer.routine_expose
        routine_descriptor_expose = default_exposer.routine_descriptor_expose

#define default.
default_exposer = Exposer()
"""This is a default instance of :class:`Exposer`. Use this (and
the module level convenience functions that refer to it) if
you have no need of multiple instances of :class:`Exposer`.
"""


default_exposer.define_module_functions()


