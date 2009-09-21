"""
shared types, functions and constants.
important - don't reload() this module, or things are likely to break
"""
from sys import excepthook, stderr

#
# the original version of the __builtins__, in case you do
# __builtin__.x = rpyc_version_of_x
#
orig_isinstance = isinstance
orig_getattr = getattr
orig_hasttr = hasattr
orig_issubclass = issubclass
orig_help = help
orig_reload = reload
orig_dir = dir
orig_excepthook = excepthook
orig_type = type


def raise_exception(typ, val, tbtext):
    """a helper for raising remote exceptions"""
    if orig_type(typ) == str:
        raise typ
    else:
        val._remote_traceback = tbtext
        raise val

class ImmDict(object):
    """immutable dict (passed by value)"""
    __slots__ = ["dict"]
    def __init__(self, dict):
        self.dict = dict
    def items(self):
        return self.dict.items()

def _get_dict(obj):
    return object.__getattribute__(obj, "____dict__")

class AttrFrontend(object):
    """a wrapper that implements the attribute protocol for a dict backend"""
    __slots__ = ["____dict__"]
    
    def __init__(self, dict):
        object.__setattr__(self, "____dict__", dict)
        
    def __delitem__(self, name):
        del _get_dict(self)[name]
    def __getitem__(self, name):
        return _get_dict(self)[name]
    def __setitem__(self, name, value):
        _get_dict(self)[name] = value

    __delattr__ = __delitem__
    __getattr__ = __getitem__
    __setattr__ = __setitem__

    def __repr__(self):
        return "<AttrFrontend(%s)>" % (", ".join(_get_dict(self).keys()),)


def rpyc_excepthook(exctype, value, traceback):
    if hasattr(value, "_remote_traceback"):
        print >> stderr, "======= Remote traceback ======="
        print >> stderr, value._remote_traceback
        print >> stderr, "======= Local exception ======="
        orig_excepthook(exctype, value, traceback)
    else:
        orig_excepthook(exctype, value, traceback)

