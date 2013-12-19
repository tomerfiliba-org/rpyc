try:
    import __builtin__
except ImportError:
    import builtins as __builtin__
import opcode
from types import CodeType, FunctionType
from rpyc.core import brine

CODEOBJ_MAGIC = "MAg1c J0hNNzo0hn ZqhuBP17LQk8"


def decode_codeobj(codeobj):
    if hasattr(codeobj, "func_code"):
        codeobj = codeobj.func_code
    extended_arg = 0
    codestr = codeobj.co_code
    free = None
    i = 0
    while i < len(codestr):
        op = ord(codestr[i])
        opname = opcode.opname[op]
        i += 1
        argval = None
        if op >= opcode.HAVE_ARGUMENT:
            oparg = ord(codestr[i]) + ord(codestr[i + 1]) * 256 + extended_arg
            i += 2
            extended_arg = 0
            if op == opcode.EXTENDED_ARG:
                extended_arg = oparg * 65536
                continue
            
            if op in opcode.hasconst:
                argval = codeobj.co_consts[oparg]
            elif op in opcode.hasname:
                argval = codeobj.co_names[oparg]
            elif op in opcode.hasjrel:
                argval = i + oparg
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

    for op, arg in decode_codeobj(cobj):
        if op in ("LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL"):
            if arg not in __builtin__.__dict__:
                raise TypeError("Cannot export a function with non-builtin globals: %r" % (arg,))

    exported = (cobj.co_argcount, cobj.co_nlocals, cobj.co_stacksize, cobj.co_flags,
        cobj.co_code, tuple(consts2), cobj.co_names, cobj.co_varnames, cobj.co_filename,
        cobj.co_name, cobj.co_firstlineno, cobj.co_lnotab, cobj.co_freevars, cobj.co_cellvars)
    assert brine.dumpable(exported)
    return (CODEOBJ_MAGIC, exported)

def export_function(func):
    if func.func_closure:
        raise TypeError("Cannot export a function closure")
    if not brine.dumpable(func.func_defaults):
        raise TypeError("Cannot export a function with non-brinable defaults (func_defaults)")
    
    return func.__name__, func.__module__, func.func_defaults, _export_codeobj(func.func_code)[1]

def _import_codetup(codetup):
    (argcnt, nloc, stk, flg, codestr, consts, names, varnames, filename, name,
        firstlineno, lnotab, freevars, cellvars) = codetup

    consts2 = []
    for const in consts:
        if isinstance(const, tuple) and len(const) == 2 and const[0] == CODEOBJ_MAGIC:
            consts2.append(_import_codetup(const[1]))
        else:
            consts2.append(const)

    return CodeType(argcnt, nloc, stk, flg, codestr, tuple(consts2), names, varnames, filename, name,
        firstlineno, lnotab, freevars, cellvars)

def import_function(functup):
    name, modname, defaults, codetup = functup
    mod = __import__(modname, None, None, "*")
    codeobj = _import_codetup(codetup)
    return FunctionType(codeobj, mod.__dict__, name, defaults)


