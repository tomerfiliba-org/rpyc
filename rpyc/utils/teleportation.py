import opcode
import sys
try:
    import __builtin__
except ImportError:
    import builtins as __builtin__  # noqa: F401
from rpyc.lib.compat import is_py_3k, is_py_gte38
from types import CodeType, FunctionType
from rpyc.core import brine
from rpyc.core import netref

CODEOBJ_MAGIC = "MAg1c J0hNNzo0hn ZqhuBP17LQk8"


# NOTE: dislike this kind of hacking on the level of implementation details,
# should search for a more reliable/future-proof way:
CODE_HAVEARG_SIZE = 2 if sys.version_info >= (3, 6) else 3
try:
    from dis import _unpack_opargs
except ImportError:
    # COPIED from 3.5's `dis.py`, this should hopefully be correct for <=3.5:
    def _unpack_opargs(code):
        extended_arg = 0
        n = len(code)
        i = 0
        while i < n:
            op = code[i]
            offset = i
            i = i + 1
            arg = None
            if op >= opcode.HAVE_ARGUMENT:
                arg = code[i] + code[i + 1] * 256 + extended_arg
                extended_arg = 0
                i = i + 2
                if op == opcode.EXTENDED_ARG:
                    extended_arg = arg * 65536
            yield (offset, op, arg)


def decode_codeobj(codeobj):
    # adapted from dis.dis
    if is_py_3k:
        codestr = codeobj.co_code
    else:
        codestr = [ord(ch) for ch in codeobj.co_code]
    free = None
    for i, op, oparg in _unpack_opargs(codestr):
        opname = opcode.opname[op]
        if oparg is not None:
            if op in opcode.hasconst:
                argval = codeobj.co_consts[oparg]
            elif op in opcode.hasname:
                argval = codeobj.co_names[oparg]
            elif op in opcode.hasjrel:
                argval = i + oparg + CODE_HAVEARG_SIZE
            elif op in opcode.haslocal:
                argval = codeobj.co_varnames[oparg]
            elif op in opcode.hascompare:
                argval = opcode.cmp_op[oparg]
            elif op in opcode.hasfree:
                if free is None:
                    free = codeobj.co_cellvars + codeobj.co_freevars
                argval = free[oparg]

        yield (opname, argval)


def _export_codeobj(cobj):
    consts2 = []
    for const in cobj.co_consts:
        if brine.dumpable(const):
            consts2.append(const)
        elif isinstance(const, CodeType):
            consts2.append(_export_codeobj(const))
        else:
            raise TypeError("Cannot export a function with non-brinable constants: %r" % (const,))

    if is_py_gte38:
        # Constructor was changed in 3.8 to support "advanced" programming styles
        exported = (cobj.co_argcount, cobj.co_posonlyargcount, cobj.co_kwonlyargcount, cobj.co_nlocals,
                    cobj.co_stacksize, cobj.co_flags, cobj.co_code, tuple(consts2), cobj.co_names, cobj.co_varnames,
                    cobj.co_filename, cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab, cobj.co_freevars,
                    cobj.co_cellvars)
    elif is_py_3k:
        exported = (cobj.co_argcount, cobj.co_kwonlyargcount, cobj.co_nlocals, cobj.co_stacksize, cobj.co_flags,
                    cobj.co_code, tuple(consts2), cobj.co_names, cobj.co_varnames, cobj.co_filename,
                    cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab, cobj.co_freevars, cobj.co_cellvars)
    else:
        exported = (cobj.co_argcount, cobj.co_nlocals, cobj.co_stacksize, cobj.co_flags,
                    cobj.co_code, tuple(consts2), cobj.co_names, cobj.co_varnames, cobj.co_filename,
                    cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab, cobj.co_freevars, cobj.co_cellvars)

    assert brine.dumpable(exported)
    return (CODEOBJ_MAGIC, exported)


def export_function(func):
    if is_py_3k:
        func_closure = func.__closure__
        func_code = func.__code__
        func_defaults = func.__defaults__
    else:
        func_closure = func.func_closure
        func_code = func.func_code
        func_defaults = func.func_defaults

    if func_closure:
        raise TypeError("Cannot export a function closure")
    if not brine.dumpable(func_defaults):
        raise TypeError("Cannot export a function with non-brinable defaults (func_defaults)")

    return func.__name__, func.__module__, func_defaults, _export_codeobj(func_code)[1]


def _import_codetup(codetup):
    if is_py_3k:
        # Handle tuples sent from 3.8 as well as 3 < version < 3.8.
        if len(codetup) == 16:
            (argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames,
             filename, name, firstlineno, lnotab, freevars, cellvars) = codetup
        else:
            (argcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames,
             filename, name, firstlineno, lnotab, freevars, cellvars) = codetup
            posonlyargcount = 0
    else:
        (argcount, nlocals, stacksize, flags, code, consts, names, varnames,
         filename, name, firstlineno, lnotab, freevars, cellvars) = codetup

    consts2 = []
    for const in consts:
        if isinstance(const, tuple) and len(const) == 2 and const[0] == CODEOBJ_MAGIC:
            consts2.append(_import_codetup(const[1]))
        else:
            consts2.append(const)
    consts = tuple(consts2)
    if is_py_gte38:
        codetup = (argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames,
                   filename, name, firstlineno, lnotab, freevars, cellvars)
    elif is_py_3k:
        codetup = (argcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames, filename, name,
                   firstlineno, lnotab, freevars, cellvars)
    else:
        codetup = (argcount, nlocals, stacksize, flags, code, consts, names, varnames, filename, name, firstlineno,
                   lnotab, freevars, cellvars)
    return CodeType(*codetup)


def import_function(functup, globals=None, def_=True):
    name, modname, defaults, codetup = functup
    if globals is None:
        try:
            mod = __import__(modname, None, None, "*")
        except ImportError:
            mod = __import__("__main__", None, None, "*")
        globals = mod.__dict__
    # function globals must be real dicts, sadly:
    if isinstance(globals, netref.BaseNetref):
        from rpyc.utils.classic import obtain
        globals = obtain(globals)
    globals.setdefault('__builtins__', __builtins__)
    codeobj = _import_codetup(codetup)
    funcobj = FunctionType(codeobj, globals, name, defaults)
    if def_:
        globals[name] = funcobj
    return funcobj
