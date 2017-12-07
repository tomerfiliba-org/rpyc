"""
The :mod:`rpyc.security.restrictor` module is used to do low level exposure
of objects and classes as `RPyC Exposed` objects.

Usually the :class:`Exposer <rpyc.security.exposer.Exposer>` interface
inside :mod:`rpyc.security.exposer` is used instead. However, understanding
the API at this level is useful.
"""

#THIS FILE is full of such ridiculously arcane MAGIC that it is ridiculous
#to work with. Beware all ye who enter here, there be DRAGONS here. The
#only practical way for new people to really understand this code is
#probably to try to modify it, break it a lot, running it frequently
#against the test suites, which hopefully catch all the important cases.

import inspect
import types

from rpyc.security import olps
from rpyc.security import exceptions
from rpyc.security.utility import get_olp
from rpyc.lib.colls import WeakIdMap
from rpyc.lib.compat import basestring, is_py3k, py_get_func

#This is used to mark a vaue as exposed in various
#__repr__ functions. We also call it in test code
#to make sure the mark is showing up.
def exposed_mark(value):
    if not isinstance(value, basestring):
        raise TypeError("Input to exposed_mark "
                      + " must be str type")
    if value[0:1] == "<" and value[-1:] == ">":
        return value[:-1] + " (RPyC exposed)>"
    else:
        return value + " (RPyC exposed)"

def _force_metaclass(cls, meta):
    # python 2 and 3 compatible metaclasses..
    ns = dict(cls.__dict__)
    return meta(cls.__name__, cls.__bases__, ns)

class SecurityClassRestrictor(object):
    accessors = set(["_rpyc_getattr", "_rpyc_setattr", "_rpyc_delattr"])

    def __init__(self):
        self._secured_classes = WeakIdMap()
        self._default_profiles = WeakIdMap()
        self._instance_restrictor = None

    def set_instance_restrictor(self, instance_restrictor):
        self._instance_restrictor = instance_restrictor

    #Mark is used to determine if the instance __repr__ function
    #will be exposed_mark'd.   It has no effect on the class mark
    #it is passed in here solely so it can be passed to instances
    def __call__(self, obj, olp,
                 default = False):
        security_enabled = False

        def _secure_getattr(cls, name, secured = True):
            #These are always visible.
            if name == "_rpyc__exposed__":
                return id(cls)
            elif name == "_rpyc__unwrapped_id__":
                return id(obj)
            elif name == "_rpyc__olp__":
                if secured:
                    return olp.read_only_copy()
                else:
                    return olp

            accessors = SecurityClassRestrictor.accessors
            if name in accessors:
                return type.__getattribute__(class_value, name)

            if security_enabled and secured:
                olp.cls_getattr_check(obj, name)

            if name == "_rpyc__unwrapped__":
                return obj

            #We do not defer class accesses to
            #obj._rpyc_getattr -- even if it exists
            #because under the old usage--the class
            #version of rpyc_???attr was a method
            #used for accessing the instance (the
            #first parameter needs to be the instance).
            #Calling it will not work, unless
            #The implementer used a metaclass, a class
            #method, or checks "self" to see if it is the
            #class. Old implementations will break, because
            #the argument count is wrong.

            return_value = getattr(obj, name)
            return return_value

        def _secure_setattr(cls, name, value, secured = True):
            if security_enabled and secured:
                olp.cls_setattr_check(obj, name, value)

            #We do not defer class accesses to
            #obj._rpyc_setattr -- even if it exists
            #for similar reasons I don't vector
            #to obj._rpyc_getattr above.
            #
            #Fine for the instance/bad for the class

            setattr(obj, name, value)

        def _secure_delattr(cls, name, secured = True):
            if security_enabled and secured:
                olp.cls_delattr_check(obj, name)

            #We do not defer class accesses to
            #obj._rpyc_delattr -- even if it exists
            #for similar reasons I don't vector
            #to obj._rpyc_getattr above.
            #
            #Fine for the instance/bad for the class
            delattr(obj, name)

        class FakeType(type):
            def __repr__(cls, *arg, **kwargs):
                obj_class = type(obj)
                obj_class_class = type(obj_class)
                return_value = obj_class_class.__repr__(obj_class,
                                                        *arg, **kwargs)
                return return_value

        #We will add the metaclass FakeType to this
        class SecureType(type):
            __name__ = type.__name__
            __module__ = type.__module__
            if hasattr(type, "__qualname__"): #for python 2
                __qualname__ = type.__qualname__

            #THIS IS INVOKED when subclassing, which is
            #good. we can replace bases.
            def __new__(cls, name, bases, dict):
                #Okay, need actual classes.
                new_bases = []
                subtyped = False
                for base in bases:
                    #Do not inherit a secure type, it will not work
                    # _PyObject_GenericGetAttr and type_getattro
                    # in the CPython C source code will both
                    # use PyType_Lookup -- and it will not
                    # use __getattribute__ to get the __dict__.
                    # It is possible to reimplement type_getattro
                    # in python, but _PyObject_GenericGetAttr
                    # on an instance will still kill you, as
                    # it will happily bypass all possible ways
                    # to hook and change its behaviour.  It will
                    # prevent you from using any variable/method
                    # defined in a secure class because the proxy
                    # will not and cannot have its own internal
                    # __dict__ set right.
                    #
                    # So when inheriting, we change the class.
                    try:
                        true_class = \
                            super(SecureType, base).__getattribute__("_rpyc__true_class__")
                        if true_class == obj: # pragma: no branch
                                              # This will always be true except under very
                                              # weird circumstances because every time we are
                                              # inherited we de-proxy.
                            subtyped = True
                    except (AttributeError, TypeError):
                        true_class = base # pragma: no branch
                    new_bases.append(true_class)
                if subtyped: #Bypass this class altogether.
                             #This is so important. inheritance will
                             #break badly without it.
                    if isinstance(obj, type):
                        return type(name, tuple(new_bases), dict)
                    else:
                        #old style python objects.
                        return type(obj)(name, tuple(new_bases), dict)
                else:
                    try:
                        return type.__new__(cls, name, tuple(new_bases), dict)
                    except TypeError:
                        #python2 classobj type then.
                        #We still simulate it with a new style object.
                        return type.__new__(cls, name, tuple(new_bases+[object]), dict)

            def __init__(cls, name, bases, dict):
                super(SecureType, cls).__init__(name, bases, dict)
                super(SecureType, cls).__setattr__("_rpyc__true_class__", obj)

            def __repr__(cls, *arg, **kwargs):
                return exposed_mark(repr(obj))

            def __hash__(cls):
                return hash(obj)

            #Weird format to make this work as metaclass function.
            def __eq__(cls, other_value):
                try:
                    other_id = other_value._rpyc__unwrapped_id__
                except AttributeError:
                    other_id = id(other_value)

                return (id(class_value) == other_id) or \
                       (id(obj) == other_id)

            def __dir__(cls):
                if cls is class_value:
                    obj_dir = dir(obj)
                    obj_dir += list(SecurityClassRestrictor.accessors)
                else:
                    obj_dir = type(obj).__dir__(cls)

                final_dir = list(set(obj_dir)) #deduplicate
                return sorted(final_dir)

            #This makes magical exposed construction happen.
            def __call__(cls, *args, **kwargs):
                #This is probably only necessary to ensure lock_local
                #calls.

                #remote side is required to break this into a
                #getattr(__call__) and then call it.
                if security_enabled and olp.lock_local:
                    olp.cls_getattr_check(obj, "__call__")

                #return_value = obj.__call__(*args, **kwargs)
                return_value = obj(*args, **kwargs)
                #self here is from wrapping object--not a typo
                return self._instance_restrictor(return_value, olp)

            #DO NOT RENAME THIS, this is critical to RPYC security
            def _rpyc_getattr(cls, name):
                return _secure_getattr(cls, name, secured = True)

            def __getattribute__(cls, name):
                return _secure_getattr(cls, name, secured = olp.lock_local)

            #No need for __getattr__ for fake class, just use __getattribute__

            #DO NOT RENAME THIS, this is critical to RPYC security
            def _rpyc_setattr(cls, name, value):
                return _secure_setattr(cls, name, value,
                                       secured = True)

            def __setattr__(cls, name, value):
                return _secure_setattr(cls, name, value,
                                       secured = olp.lock_local)

            #DO NOT RENAME THIS, this is critical to RPYC security
            def _rpyc_delattr(cls, name):
                return _secure_delattr(cls, name, secured = True)

            def __delattr__(cls, name):
                return _secure_delattr(cls, name, secured = olp.lock_local)

            def __subclasscheck__(cls, other):
                #is other a subclass of cls?
                return issubclass(other, obj) or super(SecureType, cls).__subclasscheck__(other)

            def __instancecheck__(cls, other):
                return isinstance(other, obj) or super(SecureType, cls).__instancecheck__(other)

        #Add FakeType metaclass
        SecureType = _force_metaclass(SecureType, FakeType)

        #will be adding SecureType as metaclass of SecurityRestrictedClass
        try:
            class SecurityRestrictedClass(obj):
                pass
        except TypeError: #not acceptable base type.
            #Old version of this code:
            #   class SecurityRestrictedClass(*obj.__bases__):
            #        pass
            #
            #However, python2 doesn't support "*" with class
            #inheritances..
            #
            #Therefore, we metaprogram.
            exec_string = "class SecurityRestrictedClass("
            base_strings = []
            for i in range(len(obj.__bases__)):
                base_strings.append("obj.__bases__[%s]" % i)
            exec_string += ", ".join(base_strings)
            exec_string += "):\n"
            exec_string += "    pass\n"
            new_locals = dict(locals())

            #Having to do this metaprogramming sucks.

            #eval/compile is used because exec syntax is incompatible between
            #python 2 & 3 when inside subfunction. Only the old style exec syntax
            #avoids the following error in python2 (before 2.7.9):
            #   ``SyntaxError: unqualified exec is not allowed in function ......`
            #The only way to avoid it is to use exec qualification using the old syntax
            #But the old syntax is syntactically illegal for Python3.
            eval(compile(exec_string, __name__+".metacode", 'exec'), globals(), new_locals)

            SecurityRestrictedClass = new_locals["SecurityRestrictedClass"]

        #Add SecureType metaclass
        SecurityRestrictedClass = \
            _force_metaclass(SecurityRestrictedClass, SecureType)

        #Register object, so we always get back same class instance with same
        #olp.
        class_value = SecurityRestrictedClass

        try:
            if obj not in self._secured_classes:
                self._secured_classes[obj] = WeakIdMap()
            if class_value not in self._secured_classes:
                self._secured_classes[class_value] = WeakIdMap()

            if olp in self._secured_classes[obj]:
                #grab previously stored instance
                class_value = self._secured_classes[obj][olp]
            else:
                self._secured_classes[obj]
                self._secured_classes[class_value]
                self._secured_classes[obj][olp] = class_value
                self._secured_classes[class_value][olp] = class_value

            if default:
                self._default_profiles[obj] = olp
                self._default_profiles[class_value] = olp
        except TypeError: # pragma: no cover
            #I have yet to encounter anything that passes the inspect.isclass test
            #that I can't WeakIdMap, but if we run into one, the correct behavior
            #is to simply ignore registration of it.
            pass

        security_enabled = True
        return class_value

    def get_default_profile_for_class(self, cls):
        return self._default_profiles[cls]

class SecurityInstanceRestrictor(object):
    accessors = set(["_rpyc_getattr", "_rpyc_setattr", "_rpyc_delattr"])

    def __init__(self):
        self.secured_instances = WeakIdMap()
        self.class_restrictor = None

    def set_class_restrictor(self, class_restrictor):
        self.class_restrictor = class_restrictor

    def __call__(self, obj, olp,
                 default = False):

        outer_self = self
        security_enabled = False

        def _secure_getattr(self, name, secured = True):
            #These are always visible.
            if name == "_rpyc__exposed__":
                return id(self) #For comparison purposes to see if wrapped.
            elif name == "_rpyc__unwrapped_id__":
                return id(obj)
            elif name == "_rpyc__olp__":
                if secured:
                    return olp.read_only_copy()
                else:
                    return olp

            accessors = SecurityInstanceRestrictor.accessors
            if name in accessors:
                return super(SecurityRestrictedProxy, self).__getattribute__(name)

            if security_enabled and secured:
                olp.getattr_check(obj, name)

            #Only if allowed
            if name == "_rpyc__unwrapped__":
                return obj

            if security_enabled and secured:
                if hasattr(obj, "_rpyc_getattr"):
                    use_rpyc_getattr=True

                    #Really weird descriptor case that you won't understand
                    #unless you try this code without it.
                    #Only checking it in get case because only really issue
                    #there unless something perverse is going on
                    if inspect.isroutine(obj):
                        try:
                            func_getattr = py_get_func(obj)._rpyc_getattr
                            #is won't work
                            if (func_getattr == obj._rpyc_getattr):
                                use_rpyc_getattr = False

                        except AttributeError:
                            #not the problem case, move on
                            pass

                    if use_rpyc_getattr:
                        return obj._rpyc_getattr(name)

            #Do class replacement
            if name == "__class__":
                return class_value

            #Maybe should make a version of dir
            #that only shows accessible ones.
            if name == "__dir__":
                return super(SecurityRestrictedProxy, self).__getattribute__(name)

            return_value = getattr(obj, name)
            return return_value

        def _secure_setattr(self, name, value, secured = True):
            if name == "__class__":
                #don't worry about deletions--it is blocked anyways.
                raise AttributeError('Cannot set "__class__" of RPyC exposed object.')
            if security_enabled and secured:
                olp.setattr_check(obj, name, value)

                if hasattr(obj, "_rpyc_setattr"):
                    #Defer to that function.
                    obj._rpyc_setattr(name, value)
                    return

            setattr(obj, name, value)

        def _secure_delattr(self, name, secured=True):
            if security_enabled and secured:
                olp.delattr_check(obj, name)
                if hasattr(obj, "_rpyc_delattr"):
                    #Defer to that function.
                    obj._rpyc_delattr(name)
                    return

            delattr(obj, name)

        class FakeType(type):
            def __repr__(cls, *arg, **kwargs):
                return_repr = exposed_mark(repr(type(obj)))
                return return_repr

            def __eq__(cls, value):
                return value == class_value

            #__hash__ has to be
            #defined to be hashable and callable
            #by certain forms of inspection
            def __hash__(cls):
                return hash(class_value)

            #This is here to prevent type() from exposing
            #a whole bunch of modifiable things.
            def __getattribute__(cls, name):
                if name == "_rpyc__exposed__":
                    return id(cls)
                elif name in ["__repr__", "__eq__", "__hash__"]:
                    return super(FakeType, cls).__getattribute__(name)
                return getattr(class_value, name)

            def __setattr__(cls, name, value):
                return setattr(class_value, name, value)

            def __delattr__(cls, name):
                return delattr(class_value, name)

        #Will be adding FakeType metaclass
        class SecurityRestrictedProxy(object):
            #Has to be here or isn't callable.
            def __call__(self, *args, **kwargs):
                return obj.__call__(*args, **kwargs)

            #DO NOT RENAME THIS, this is critical to RPYC security
            def _rpyc_getattr(self, name):
                return _secure_getattr(self, name, secured = True)

            def __getattribute__(self, name):
                return _secure_getattr(self, name, secured = olp.lock_local)

            #if __getattribute__ fails with attribute error,
            #this is called.
            def __getattr__(self, name):
                return _secure_getattr(self, name, secured = olp.lock_local)

            #DO NOT RENAME THIS, this is critical to RPYC security
            def _rpyc_setattr(self, name, value):
                return _secure_setattr(self, name, value, secured = True)

            def __setattr__(self, name, value):
                return _secure_setattr(self, name, value,
                                       secured = olp.lock_local)

            #DO NOT RENAME THIS, this is critical to RPYC security
            def _rpyc_delattr(self, name):
                return _secure_delattr(self, name, secured = True)

            def __delattr__(self, name):
                return _secure_delattr(self, name, secured = olp.lock_local)

            def __repr__(self, *arg, **kwargs):
                if is_py3k:
                    repr_value = obj.__repr__(*arg, **kwargs)
                else:
                    repr_value = repr(obj)

                if olp.mark:
                    repr_value = exposed_mark(repr_value)
                return repr_value

            #This is like __call__, if not defined, builtin code fails.
            #for function binding we need this.
            def __get__(self, bind_obj, bind_type=None):
                value = obj.__get__(bind_obj, bind_type)
                if inspect.isroutine(obj):
                    #deal with function/method binding
                    new_olp = olp #use same olp as us if we
                                  #are func itself.

                    func_found = False
                    try:
                        func = py_get_func(obj)
                        func_found = True
                    except AttributeError:
                        pass

                    if func_found:
                        try:
                            new_olp = get_olp(func)
                        except (AttributeError, ValueError):
                            #approprate OLP wasn't found
                            new_olp=None
                    else:
                        #the __get__ for python2 for class
                        #is problematic. When we wrap it
                        #__get__ still returns original
                        #version.
                        if not is_py3k:
                            if type(value) == types.UnboundMethodType:
                                if py_get_func(value) is not self:
                                    value = types.UnboundMethodType(self, bind_obj, bind_type)

                    if new_olp != None:
                        #expose new binding same as this one.
                        return outer_self.__call__(value, new_olp)
                return value

            def __dir__(self):
                obj_dir = dir(obj)
                #set is to remove duplicates.
                final_dir = list(set(obj_dir
                               + list(SecurityInstanceRestrictor.accessors)))
                return sorted(final_dir)

        #Add FakeType metaclass
        SecurityRestrictedProxy = \
            _force_metaclass(SecurityRestrictedProxy, FakeType)

        class_value = self.class_restrictor(obj.__class__,
                                            olp,
                                            default=default)

        security_enabled = True

        created = False

        #If the object can be weakref'd we can ensure that
        #calling this on the object again, with the same olp
        #returns the exact same object.
        try:
            if obj not in self.secured_instances:
                return_value = SecurityRestrictedProxy()
                created = True
                self.secured_instances[obj] = WeakIdMap()
                self.secured_instances[return_value] = WeakIdMap()

            if olp in self.secured_instances[obj]:
                #grab previously stored instance
                return_value = self.secured_instances[obj][olp]
                created = True
            else:
                if not created:
                    return_value = SecurityRestrictedProxy()
                    created = True
                self.secured_instances[obj][olp] = return_value
                self.secured_instances[return_value] = WeakIdMap()
                self.secured_instances[return_value][olp] = return_value
        except TypeError: # pragma: no cover
            #Most likely object couldn't be weak ref'd.
            #The best we can do is return a new security wrapped
            #version--at least the insides will proxy to the same
            #object.
            #
            #It will not pass the "is" test with other instances of
            #itself with the same olp, but it should pass "=="
            pass
        if not created: # pragma: no cover
            #it is remotely possible that this generates a type error.
            return_value = SecurityRestrictedProxy()
        return return_value

class SecurityRestrictor(object):
    """This class is used to create `RPyC Exposed` values.
    Normally only one is needed (a singleton) and in that case you should
    use the
    :data:`security_restrict <rpyc.security.restrictor.security_restrict>`
    instance provided. Most users should have no need to instantiate this
    class themselves.
    """
    def __init__(self):
        class_restrictor = \
            SecurityClassRestrictor()

        self._class_restrictor = class_restrictor

        instance_restrictor = \
            SecurityInstanceRestrictor()

        self._instance_restrictor = instance_restrictor

        class_restrictor.set_instance_restrictor(instance_restrictor)
        instance_restrictor.set_class_restrictor(class_restrictor)

    #Set default to True if you want this to be the default OLP for the class
    def __call__(self, obj, olp = None,
                  default = False): #Don't document default yet
        """
        Create a `RPyC exposed` version of `obj`

        :param obj: Instance or class to create `RPyC Exposed` proxy for
        :param olp: An
            :class:`OLP <rpyc.security.olps.OLP>`
            specifying how the attributes of ``obj`` are to be accessed
        :param bool default: Whether to store ``olp`` as the default for
            the class
        :return: `RPyC Exposed` version of ``obj``

        This method is simple: pass in ``obj`` and ``olp`` and receive
        the `RPyC Exposed` version of ``obj``.

        If ``obj`` is a type that can be weak referenced, this method
        urther guarantees that calling it again with the same
        ``obj`` and ``olp`` will yield the exact same
        `RPyC Exposed` value.

        if ``olp`` is set to ``None``, a default
        :class:`OLP <rpyc.security.olps.OLP>`
        will be instantiated that does not yet allow access to anything.

        The ``default`` parameter is a boolean used to signify that the
        ``olp`` parameter should be used as the default :class:`OLP` for
        the class. If ``True`` this method registers the class such that
        :meth:`get_default_profile_for_class`
        will return ``olp`` when passed in the class in question.

        The :class:`Exposer <rpyc.security.exposer.Exposer>` class uses
        this registry to determine what :class:`OLP` to inherit from when
        the ``inherit`` arg to
        :func:`@expose <rpyc.security.exposer.Exposer.decorate>` is specified
        as a class.
        """

        if olp is None:
            olp = olps.OLP()

        if inspect.isclass(obj):
            return self._class_restrictor(obj,
                                          olp,
                                          default = default)
        else:
            return self._instance_restrictor(obj,
                                             olp,
                                             default = default)

    #This can only be set by calling with default=True
    def get_default_profile_for_class(self, cls):
        """Returns the last
        :class:`OLP <rpyc.security.olps.OLP>`
        associated as the default for ``cls``

        :param cls: Class you want to get default :class:`OLP` for
        :return: The :class:`OLP` registered
        :raises KeyError: if cls does not have a default registered :class:`OLP`

        This returns the
        :class:`OLP <rpyc.security.olps.OLP>` last
        registered as the `default` via a call to
        :class:`SecurityRestrictor <rpyc.security.restrictor.SecurityRestrictor>`
        """
        return self._class_restrictor.get_default_profile_for_class(cls)

security_restrict = SecurityRestrictor()
"""The default instance of
:class:`SecurityRestrictor <rpyc.security.restrictor.SecurityRestrictor>`
that should be used unless there is a compelling case to have multiple
instantiations of :class:`SecurityRestrictor`."""

