"""
Default OLP base definitions for common Python objects
"""

from rpyc.lib.compat import is_py3k
from rpyc.security import locks
from rpyc.security import olps

class Profiles(object):
    def __init__(self):
        #It is very important that I don't expose anything whose members
        #might be modifiable. For that reason I don't expose __defaults__
        shared_base = ["__dir__", "__doc__", "__eq__", "__format__",
                       "__ge__", "__gt__", "__hash__", "__le__", "__lt__",
                       "__ne__", "__repr__", "__sizeof__", "__str__", "__subclasshook__"]
        name_base =["__module__", "__name__", "__qualname__"]
        common_base = shared_base + name_base

        #Auto exposed class values--expose very little here
        #because user classes can do a lot.
        self._class_exposed = ["__doc__"] + list(name_base) #That is all.

        #Auto exposed instance methods of exposed classes
        self._instance_exposed = \
            ["__module__", "__class__"]  #__class__ when grabbed will
                                         #return secured class.

        #__text_signature__ is only in builtins.
        self._routine_exposed = \
            list(common_base) +  ["__call__", "__text_signature__"]
        if not is_py3k:
            self._routine_exposed += ["func_doc", "func_name"]

        self._routine_descriptor_exposed = \
            list(shared_base) +  ["__class__", "__isabstractmethod__"]

        #_generator_exposed and _coroutine_exposed isn't currently actually
        #used--but is there for future support of auto-promoting generators
        #returned.

        #We could add "throw" to these lists but too much potential for abuse.
        #that throws an arbritary exception into the generator.
        self._generator_exposed = \
            list(common_base) + ["__iter__", "close", "send", "gi_running"]
        if is_py3k:
            self._generator_exposed += ["__next__"]
        else:
            self._generator_exposed += ["next"]

        self._coroutine_exposed = \
            list(common_base) + ["__await__", "close", "send", "cr_running"]

    def _sanitize_exposed_list(self, property_name, value):
        try:
            value = list(value)
        except TypeError:
            raise ValueError("%s must be set to an iterable list of strings" % property_name)
        new_list = []
        for item in value:
            try:
                item = olps.sanitize_attr_key(item)
            except (ValueError, TypeError) as e:
                raise ValueError("items in %s must be valid python identifiers" % property_name)
            new_list.append(item)
        return new_list

    @property
    def class_exposed(self):
        return self._class_exposed

    @class_exposed.setter
    def class_exposed(self, value):
        self._class_exposed = \
            self._sanitize_exposed_list("class_exposed", value)

    @property
    def instance_exposed(self):
        return self._instance_exposed

    @instance_exposed.setter
    def instance_exposed(self, value):
        self._instance_exposed = \
            self._sanitize_exposed_list("instance_exposed", value)

    @property
    def routine_exposed(self):
        return self._routine_exposed

    @routine_exposed.setter
    def routine_exposed(self, value):
        self._routine_exposed = \
            self._sanitize_exposed_list("routine_exposed", value)

    @property
    def routine_descriptor_exposed(self):
        return self._routine_descriptor_exposed

    @routine_descriptor_exposed.setter
    def routine_descriptor_exposed(self, value):
        self._routine_descriptor_exposed = \
            self._sanitize_exposed_list("routine_descriptor_exposed", value)

    @property
    def generator_exposed(self):
        return self._generator_exposed

    @generator_exposed.setter
    def generator_exposed(self, value):
        self._generator_exposed = \
            self._sanitize_exposed_list("generator_exposed", value)

    @property
    def coroutine_exposed(self):
        return self._coroutine_exposed

    @coroutine_exposed.setter
    def coroutine_exposed(self, value):
        self._coroutine_exposed = \
            self._sanitize_exposed_list("coroutine_exposed", value)

    def items_get_olp(self, lock_list = [], items = [], cls_items=[]):
        getattr_locks = {}
        cls_getattr_locks = {}
        lock_list = locks.sanitize_and_copy_lock_list(lock_list)

        for value in items:
            getattr_locks[value] = lock_list
        for value in cls_items:
            cls_getattr_locks[value] = lock_list

        olp=olps.OLP(getattr_locks = getattr_locks,
                     cls_getattr_locks = cls_getattr_locks)
        return olp

    def create_class_olp(self, value, lock = None):
        lock_list = locks.sanitize_lock_parameter(lock)

        return self.items_get_olp(lock_list = lock_list,
                                  items = self._instance_exposed,
                                  cls_items = self.class_exposed)

    def create_routine_olp(self, value, lock = None):
        lock_list = locks.sanitize_lock_parameter(lock)

        return self.items_get_olp(lock_list = lock_list,
                                  items = self.routine_exposed)

    def create_routine_descriptor_olp(self, value, lock = None):
        lock_list = locks.sanitize_lock_parameter(lock)

        return self.items_get_olp(lock_list = lock_list,
                                  items = self.routine_descriptor_exposed)

    #Not used or tested yet, here for future use.
    def create_generator_olp(self, value, lock = None):
        lock_list = locks.sanitize_lock_parameter(lock)

        return self.items_get_olp(lock_list = lock_list,
                                  items = self.generator_exposed)

    #Not used or tested yet, here for future use.
    def create_coroutine_olp(self, value, lock = None):
        lock_list = locks.sanitize_lock_parameter(lock)

        return self.items_get_olp(lock_list = lock_list,
                                  items = self.coroutine_exposed)

default_profiles = Profiles()
