import opcode

from rpyc.lib.compat import is_py_gte38
from types import CodeType, FunctionType
from rpyc.core import brine, netref
from dis import _unpack_opargs

CODEOBJ_MAGIC = "MAg1c J0hNNzo0hn ZqhuBP17LQk8"


# NOTE: dislike this kind of hacking on the level of implementation details,
# should search for a more reliable/future-proof way:
CODE_HAVEARG_SIZE = 3


def decode_codeobj(codeobj):
    # adapted from dis.dis
    codestr = codeobj.co_code
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
            raise TypeError(f"Cannot export a function with non-brinable constants: {const!r}")

    if is_py_gte38:
        # Constructor was changed in 3.8 to support "advanced" programming styles
        exported = (cobj.co_argcount, cobj.co_posonlyargcount, cobj.co_kwonlyargcount, cobj.co_nlocals,
                    cobj.co_stacksize, cobj.co_flags, cobj.co_code, tuple(consts2), cobj.co_names, cobj.co_varnames,
                    cobj.co_filename, cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab, cobj.co_freevars,
                    cobj.co_cellvars)
    else:
        exported = (cobj.co_argcount, cobj.co_kwonlyargcount, cobj.co_nlocals, cobj.co_stacksize, cobj.co_flags,
                    cobj.co_code, tuple(consts2), cobj.co_names, cobj.co_varnames, cobj.co_filename,
                    cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab, cobj.co_freevars, cobj.co_cellvars)
    assert brine.dumpable(exported)
    return (CODEOBJ_MAGIC, exported)


def export_function(func):
    closure = func.__closure__
    code = func.__code__
    defaults = func.__defaults__
    kwdefaults = func.__kwdefaults__
    if kwdefaults is not None:
        kwdefaults = tuple(kwdefaults.items())

    if closure:
        raise TypeError("Cannot export a function closure")
    if not brine.dumpable(defaults):
        raise TypeError("Cannot export a function with non-brinable defaults (__defaults__)")
    if not brine.dumpable(kwdefaults):
        raise TypeError("Cannot export a function with non-brinable defaults (__kwdefaults__)")

    return func.__name__, func.__module__, defaults, kwdefaults, _export_codeobj(code)[1]


def _import_codetup(codetup):
    # Handle tuples sent from 3.8 as well as 3 < version < 3.8.
    if len(codetup) == 16:
        (argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames,
         filename, name, firstlineno, lnotab, freevars, cellvars) = codetup
    else:
        (argcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames,
         filename, name, firstlineno, lnotab, freevars, cellvars) = codetup
        posonlyargcount = 0

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
    else:
        codetup = (argcount, kwonlyargcount, nlocals, stacksize, flags, code, consts, names, varnames, filename, name,
                   firstlineno, lnotab, freevars, cellvars)
    return CodeType(*codetup)


def import_function(functup, globals=None, def_=True):
    name, modname, defaults, kwdefaults, codetup = functup
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
    if kwdefaults is not None:
        funcobj.__kwdefaults__ = {t[0]: t[1] for t in kwdefaults}
    if def_:
        globals[name] = funcobj
    return funcobj
