"""
A library of various helpers functions and classes
"""
import logging


class MissingModule(object):
    __slots__ = ["__name"]
    def __init__(self, name):
        self.__name = name
    def __getattr__(self, name):
        raise ImportError("module %r not found" % (self.__name,))
    def __bool__(self):
        return False
    __nonzero__ = __bool__

def safe_import(name):
    try:
        mod = __import__(name, None, None, "*")
    except ImportError:
        mod = MissingModule(name)
    return mod


def setup_logger(options):
    logging_options = {}
    if options.quiet:
        logging_options['level'] = logging.ERROR
    else:
        logging_options['level'] = logging.DEBUG
    if options.logfile:
        logging_options['file'] = options.logfile
    logging.basicConfig(**logging_options)

