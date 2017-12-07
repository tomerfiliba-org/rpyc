"""
Storage for exposer and restrictor of class and object information
that automatically cleans up.
"""

#This resembles a weakref.WeakKeyDictionary,
#except for:
#1. It uses id rather that the object __hash__ and __eq__
#   functions.  It make sure that every unique object has its own
#   entry, even if "==" might be satisfied between to objects.

import gc
import weakref

class WeakIdMap(object):
    def __init__(self):
        self._dict={}

    def __setitem__(self, obj, value):
        enabled=gc.isenabled()
        gc.disable()
        try:
            #This can throw TypeError.
            #that needs to be handled above.
            weakref.ref(obj, self.silent_delete)
            self._dict[id(obj)] = value
        finally:
            if enabled:
                gc.enable()

    def __getitem__(self, obj):
        enabled=gc.isenabled()
        gc.disable()
        try:
            if id(obj) in self._dict:
                return self._dict[id(obj)]
            else:
                raise KeyError(obj) #Key is obj, not id.
        finally:
            if enabled:
                gc.enable()

    def __contains__(self, obj):
        enabled=gc.isenabled()
        gc.disable()
        try:
            return id(obj) in self._dict
        finally:
            if enabled:
                gc.enable()

    def get_by_id(self, id):
        enabled=gc.isenabled()
        gc.disable()
        try:
            return self._dict[id]
        finally:
            if enabled:
                gc.enable()

    #have to define this or "in" doesn't work. Apparently it
    #tries __getitem__ first than iterates to check (WOAH)
    #as if a list.
    #
    #We return nothing, because we don't want iteration
    #over this.
    def __iter__(self):
        return [].__iter__()

    def __len__(self):
        return len(self._dict)

    def silent_delete(self, obj):
        enabled=gc.isenabled()
        gc.disable()
        try:
            if id(obj) in self._dict:
                del(self._dict[id(obj)])
        finally:
            if enabled:
                gc.enable()

    def __delitem__(self, obj):
        enabled=gc.isenabled()
        gc.disable()
        try:
            if id(obj) in self._dict:
                del(self._dict[id(obj)])
            else:
                raise KeyError(obj)
        finally:
            if enabled:
                gc.enable()

