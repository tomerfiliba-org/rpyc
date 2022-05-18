"""Supporting functions for unit tests

The core logic of the functions `_ignore_deprecated_imports` and `import_module` is from the cpython code base:
- https://github.com/python/cpython/blob/da576e08296490e94924421af71001bcfbccb317/Lib/test/support/import_helper.py
"""
import warnings
import sys
import contextlib
import unittest


@contextlib.contextmanager
def _ignore_deprecated_imports(ignore=True):
    """Context manager to suppress package and module deprecation
    warnings when importing them.
    If ignore is False, this context manager has no effect.
    """
    if ignore:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", ".+ (module|package)",
                                    DeprecationWarning)
            yield
    else:
        yield


def import_module(name, deprecated=False, *, required_on=(), fromlist=()):
    """Import and return the module to be tested, raising SkipTest if
    it is not available.
    If deprecated is True, any module or package deprecation messages
    will be suppressed. If a module is required on a platform but optional for
    others, set required_on to an iterable of platform prefixes which will be
    compared against sys.platform.
    """
    with _ignore_deprecated_imports(deprecated):
        try:
            module = __import__(name, fromlist=fromlist)
            for a in fromlist:
                if not hasattr(module, a):
                    raise ImportError(f"cannot import name '{a}' from '{name}'")
            return module
        except ImportError as msg:
            if sys.platform.startswith(tuple(required_on)):
                raise
            raise unittest.SkipTest(str(msg))
