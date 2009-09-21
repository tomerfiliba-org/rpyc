"""
ugh, the builtin 'unittest' module sucks... 
i feel like i have to rewrite everything :)
"""
import sys
import traceback
import pdb
import code
import inspect


class FailureError(Exception):
    pass
class CannotRunError(Exception):
    pass

class BlockLogger(object):
    def __init__(self):
        self.nesting = 0
    def indent(self):
        self.nesting += 1
    def dedent(self):
        assert self.nesting >= 0
        self.nesting -= 1
    def log(self, text, *args):
        text = str(text)
        if args:
            text %= args
        print "    " * self.nesting + text

BlockLogger = BlockLogger()

class TestBase(object):
    DEBUGGER = True
    SHOW_TRACEBACK = True
    TITLE = "TEST %s"
    
    def __init__(self, **kwargs):
        self.params = kwargs
    
    @classmethod
    def run(cls, *args, **kwargs):
        return cls(*args, **kwargs)._run()
    
    def _handle_exception(self, force_tb = False):
        if self.SHOW_TRACEBACK or force_tb:
            for line in traceback.format_exception(*sys.exc_info()):
                for l in line.splitlines():
                    self.log(l.rstrip())
            print
        if self.DEBUGGER:
            pdb.post_mortem(sys.exc_info()[2])
    
    def _run(self):
        success = True
        self.log(self.TITLE, self.__class__.__name__)
        self._indent()
        try:
            try:
                self.setup()
            except CannotRunError:
                pass
            except Exception:
                success = False
                self._handle_exception(force_tb = True)
            else:
                try:
                    try:
                        self.body()
                    except Exception:
                        success = False
                        self._handle_exception()
                finally:
                    try:
                        self.cleanup()
                    except Exception:
                        success = False
                        self._handle_exception(force_tb = True)
            if success:
                self.log("SUCCESS")
            else:
                self.log("FAILURE")
        finally:
            self._dedent()
        return success
    
    def body(self):
        for name in dir(self):
            if name.startswith("step_"):
                func = getattr(self, name)
                self.log("STEP %s", name[5:])
                self._indent()
                try:
                    try:
                        func()
                    except Exception:
                        self.log("FAILED")
                        raise
                    else:
                        self.log("OK")
                finally:
                    self._dedent()
    
    def setup(self):
        pass
    def cleanup(self):
        pass
    
    def interact(self, locals = None):
        if locals is None:
            locals = inspect.stack()[1][0].f_locals
        print "-" * 50
        code.interact(banner = "", local = locals)
        print "-" * 50
    
    def debug(self):
        pdb.set_trace()
    
    def fail(self, message = None):
        if not message:
            message = "no info"
        raise FailureError(message)
    def require(self, cond, message = None):
        if not cond:
            self.fail(message = message)
    def cannot_run(self, message):
        self.log("TEST CANNOT RUN: %s", message)
        raise CannotRunError(message)
    
    def _indent(self):
        BlockLogger.indent()
    def _dedent(self):
        BlockLogger.dedent()
    def log(self, text, *args):
        BlockLogger.log(text, *args)


class TestSuite(TestBase):
    TESTS = []
    DEBUGGER = False
    SHOW_TRACEBACK = False
    TITLE = "SUITE %s"
    
    def body(self):
        for t in self.TESTS:
            if not t.run(**self.params):
                self.fail("test failed")



