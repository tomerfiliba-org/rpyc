"""
A library of various helpers functions and classes
"""
import sys
import logging


class MissingModule(object):
    __slots__ = ["__name"]
    def __init__(self, name):
        self.__name = name
    def __getattr__(self, name):
        if name.startswith("__"): # issue 71
            raise AttributeError("module %r not found" % (self.__name,))
        raise ImportError("module %r not found" % (self.__name,))
    def __bool__(self):
        return False
    __nonzero__ = __bool__

def safe_import(name):
    try:
        mod = __import__(name, None, None, "*")
    except ImportError:
        mod = MissingModule(name)
    except Exception:
        # issue 72: IronPython on Mono
        if sys.platform == "cli" and name == "signal": #os.name == "posix":
            mod = MissingModule(name)
        else:
            raise
    return mod

def setup_logger(quiet = False, logfile = None):
    opts = {}
    if quiet:
        opts['level'] = logging.ERROR
    else:
        opts['level'] = logging.DEBUG
    if logfile:
        opts['file'] = logfile
    logging.basicConfig(**opts)

