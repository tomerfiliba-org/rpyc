from __future__ import with_statement
import subprocess
import sys
import os
import rpyc
import types
import unittest
import tracemalloc
tracemalloc.start()

from rpyc.utils.teleportation import export_function, import_function
from rpyc.lib.compat import is_py_3k, is_py_gte38, is_py_gte311
from rpyc.utils.classic import teleport_function


def b(st):
    if sys.version_info[0] >= 3:
        return bytes(st, "latin-1")
    else:
        return st


def f(a):
    def g(b):
        return a + int(b)
    return g


def defaults(a=5, b="hi", c=(5.5, )):
    return a, b, c


def kwdefaults(pos=5, *, a=42, b="bye", c=(12.4, )):
    return pos, a, b, c


def h(a):
    import os
    return a * os.getpid()


def foo():
    return bar() + 1


def bar():
    return 42


class TeleportationTest(unittest.TestCase):
    def setUp(self):
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
        self.proc = subprocess.Popen([sys.executable, server_file, "--mode=oneshot", "--host=localhost", "-p0"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        line = self.proc.stdout.readline().strip()
        if not line:
            print(self.proc.stderr.read())
            self.fail("server failed to start")
        self.assertEqual(line, b("rpyc-oneshot"), "server failed to start")
        host, port = self.proc.stdout.readline().strip().split(b("\t"))
        self.conn = rpyc.classic.connect(host, int(port))

    def tearDown(self):
        self.conn.close()
        self.proc.communicate()  # clear io so resources are closed

    def test(self):
        exp = export_function(f)
        f2 = import_function(exp)
        self.assertEqual(f(6)(7), f2(6)(7))

        h2 = teleport_function(self.conn, h)
        self.assertNotEqual(h(7), h2(7))

    def test_globals(self):
        def the_answer():
            return THE_ANSWER  # noqa

        teleported = teleport_function(self.conn, the_answer)
        self.conn.namespace['THE_ANSWER'] = 42
        self.assertEqual(teleported(), 42)

        the_globals = self.conn.builtins.dict({'THE_ANSWER': 43})
        teleported2 = teleport_function(self.conn, the_answer, the_globals)
        self.assertEqual(teleported2(), 43)

    def test_def(self):
        foo_ = teleport_function(self.conn, foo)
        bar_ = teleport_function(self.conn, bar)
        self.assertEqual(foo_(), 43)
        self.assertEqual(bar_(), 42)

    def test_defaults(self):
        defaults_ = teleport_function(self.conn, defaults)
        self.assertEqual(defaults_(), defaults())

    def test_kwdefaults(self):
        kwdefaults_ = teleport_function(self.conn, kwdefaults)
        self.assertEqual(kwdefaults_(), kwdefaults())

    def test_compat(self):  # assumes func has only brineable types

        def get37_schema(cobj):
            return (cobj.co_argcount, 0, cobj.co_nlocals, cobj.co_stacksize,
                    cobj.co_flags, cobj.co_code, cobj.co_consts, cobj.co_names, cobj.co_varnames,
                    cobj.co_filename, cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab,
                    cobj.co_freevars, cobj.co_cellvars)

        def get38_schema(cobj):
            return (cobj.co_argcount, 2, cobj.co_kwonlyargcount, cobj.co_nlocals,
                    cobj.co_stacksize, cobj.co_flags, cobj.co_code, cobj.co_consts, cobj.co_names,
                    cobj.co_varnames, cobj.co_filename, cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab,
                    cobj.co_freevars, cobj.co_cellvars)

        def get311_schema(cobj):
            return (cobj.co_argcount, 2, cobj.co_kwonlyargcount, cobj.co_nlocals,
                    cobj.co_stacksize, cobj.co_flags, cobj.co_code, cobj.co_consts, cobj.co_names,
                    cobj.co_varnames, cobj.co_filename, cobj.co_name, cobj.co_qualname,
                    cobj.co_firstlineno, cobj.co_lnotab, cobj.co_exceptiontable,
                    cobj.co_freevars, cobj.co_cellvars)

        if is_py_gte38:
            pow37 = lambda x, y : x ** y  # noqa
            pow38 = lambda x, y : x ** y  # noqa
            export37 = get37_schema(pow37.__code__)
            export38 = get38_schema(pow38.__code__)
            schema37 = (pow37.__name__, pow37.__module__, pow37.__defaults__, pow37.__kwdefaults__, export37)
            schema38 = (pow38.__name__, pow38.__module__, pow38.__defaults__, pow38.__kwdefaults__, export38)
            pow37_netref = self.conn.modules["rpyc.utils.teleportation"].import_function(schema37)
            pow38_netref = self.conn.modules["rpyc.utils.teleportation"].import_function(schema38)
            self.assertEqual(pow37_netref(2, 3), pow37(2, 3))
            self.assertEqual(pow38_netref(2, 3), pow38(2, 3))
            self.assertEqual(pow37_netref(x=2, y=3), pow37(x=2, y=3))
            if is_py_gte38 and not is_py_gte311:
                pow38.__code__ = types.CodeType(*export38)  # pow38 = lambda x, y, /: x ** y
                with self.assertRaises(TypeError):  # show local behavior
                    pow38(x=2, y=3)
                with self.assertRaises(TypeError):
                    pow38_netref(x=2, y=3)
            if is_py_gte311:
                pow311 = lambda x, y : x ** y  # noqa
                export311 = get311_schema(pow311.__code__)
                schema311 = (pow311.__name__, pow311.__module__, pow311.__defaults__, pow311.__kwdefaults__, export311)
                pow311_netref = self.conn.modules["rpyc.utils.teleportation"].import_function(schema311)
                self.assertTrue(is_py_gte311)
                pow311.__code__ = types.CodeType(*export311)  # pow311 = lambda x, y, /: x ** y
                with self.assertRaises(TypeError):  # show local behavior
                    pow311(x=2, y=3)
                with self.assertRaises(TypeError):
                    pow311_netref(x=2, y=3)


if __name__ == "__main__":
    unittest.main()
