import opcode

safe_builtins = []
#safe_builtins = ['Ellipsis', 'False', 'None', 'NotImplemented', 'True', 
#    'abs', 'all', 'any', 'basestring', 'bool', 'callable', 'chr', 
#    'classmethod', 'cmp', 'complex', 'dict', 'divmod', 'enumerate', 
#    'filter', 'float', 'frozenset', 'hash', 'hex', 'int', 'isinstance', 
#    'issubclass', 'iter', 'len', 'list', 'long', 'map', 'max', 'min', 
#    'object', 'oct', 'ord', 'pow', 'property', 'range', 'raw_input', 
#    'reduce', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted', 
#    'staticmethod', 'str', 'sum', 'tuple', 'type', 'unichr', 'unicode', 
#    'vars', 'xrange', 'zip']

restricted_opcodes = ["EXEC_STMT", "IMPORT_STAR", "IMPORT_NAME", "IMPORT_FROM"]
# "BUILD_CLASS", "MAKE_FUNCTION", "MAKE_CLOSURE" --- whose globals do they access?

def disassemble(codestring):
    i = 0
    output = []
    while i < len(codestring):
        oc = ord(codestring[i])
        i += 1 if oc < opcode.HAVE_ARGUMENT else 3
        output.append(opcode.opname[oc])
    return output

def dump_code(co):
    (co.co_argcount, co.co_nlocals, co.co_stacksize, co.co_flags, co.co_code, 
    co.co_constants, co.co_names, co.co_varnames, co.co_filename, co.co_name, 
    co.co_firstlineno, co.co_lnotab, co.co_freevars, co.co_cellvars)

def dump_func(f):
    (f.code, f.globals, f.name, f.argdefs, f.closure)

def load_code(items):
    for oc in disassemble(codestring):
        if oc in restricted_opcodes:
            raise ValueError("restricted opcode %r" % (oc,))

def load_func(items):
    pass

def create_cell(obj):
    def func():
        a = obj
    return func.func_closure[0]








