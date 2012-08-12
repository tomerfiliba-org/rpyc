from cpython cimport (PyObject, PyThreadState, PyFrameObject, PyInterpreterState, 
    PyThreadState_Get, Py_XINCREF, Py_XDECREF, PyImport_AddModule, PyImport_ImportModule)


cdef extern from "Python.h":
    PyObject * _PyImport_FindExtension(char *name, char *filename)
    void _PyImportHooks_Init()
    PyObject * PyDict_New()
    PyObject * PyList_New(int length)
    PyObject * PyModule_GetDict(PyObject * mod)
    int PyDict_SetItemString(PyObject *p, char *key, PyObject *val)
    PyObject * PyDict_GetItemString(PyObject *p, char *key)
    void PySys_SetPath(char *path)
    char* Py_GetPath()
    PyObject * PyDict_Copy(PyObject * p)
    void PyErr_PrintEx(int set_last)
    void PyErr_Clear()
    PyObject * PyErr_Occurred()
    void PySys_SetObject(char * name, PyObject * obj)

ctypedef struct MyFrameObject:
    Py_ssize_t ob_refcnt
    PyObject *ob_type
    Py_ssize_t ob_size
    MyFrameObject *f_back
    PyObject *f_code
    PyObject *f_builtins
    PyObject *f_globals
    PyObject *f_locals
    PyObject **f_valuestack
    PyObject **f_stacktop
    PyObject *f_trace
    PyObject *f_exc_type
    PyObject *f_exc_value
    PyObject *f_exc_traceback
    MyThreadState *f_tstate

ctypedef struct MyInterpreterState:
    void *next
    void *tstate_head
    PyObject *modules
    PyObject *sysdict
    PyObject *builtins
    PyObject *modules_reloading
    PyObject *codec_search_path
    PyObject *codec_search_cache
    PyObject *codec_error_registry

ctypedef struct MyThreadState:
    void *next
    MyInterpreterState *interp
    MyFrameObject *frame
    int recursion_depth
    int tracing
    int use_tracing
    void * c_profilefunc
    void * c_tracefunc
    PyObject *c_profileobj
    PyObject *c_traceobj
    PyObject *curexc_type
    PyObject *curexc_value
    PyObject *curexc_traceback
    PyObject *exc_type
    PyObject *exc_value
    PyObject *exc_traceback
    PyObject *dict
    int tick_counter
    int gilstate_counter
    PyObject *async_exc 


cdef PyThreadState * main_interpreter = PyThreadState_Get()

cdef class SubInterpreter(object):
    cdef PyObject * prev_modules
    cdef PyObject * prev_modules_reloading
    cdef PyObject * prev_sysdict
    cdef PyObject * prev_builtins

    def __cinit__(self):
        self.prev_modules = NULL
        self.prev_modules_reloading = NULL
        self.prev_sysdict = NULL
        self.prev_builtins = NULL

    def __enter__(self):
        if self.prev_modules is not NULL:
            raise ValueError("Subinterpreter already active")
        
        cdef MyThreadState * tstate = <MyThreadState *>PyThreadState_Get()
        self.prev_modules = tstate.interp.modules
        self.prev_modules_reloading = tstate.interp.modules_reloading
        self.prev_sysdict = tstate.interp.sysdict
        self.prev_builtins = tstate.interp.builtins
        
        tstate.interp.modules = PyDict_New()
        tstate.interp.modules_reloading = PyDict_New()

        cdef PyObject * bimod = _PyImport_FindExtension("__builtin__", "__builtin__")
        tstate.interp.builtins = PyModule_GetDict(bimod)
        Py_XINCREF(tstate.interp.builtins)
        
        cdef MyFrameObject * f = tstate.frame
        while f is not NULL:
            #print ">>>", <int>f
            Py_XINCREF(tstate.interp.builtins)
            f.f_builtins = tstate.interp.builtins
            if f == f.f_back:
                f = NULL
            else:
                f = f.f_back
        
        cdef PyObject * sysmod = _PyImport_FindExtension("sys", "sys")
        tstate.interp.sysdict = PyModule_GetDict(sysmod)
        Py_XINCREF(tstate.interp.sysdict)

        PySys_SetObject("modules", tstate.interp.modules);
        PySys_SetPath(Py_GetPath())
        _PyImportHooks_Init()
        
        cdef PyObject * mainmod = PyImport_AddModule("__main__")
        cdef PyObject * maindict = PyModule_GetDict(mainmod)
        PyDict_SetItemString(maindict, "__builtins__", bimod)
        Py_XDECREF(bimod)
        
        PyImport_ImportModule("site")

        return self

    def __exit__(self, t, v, tb):
        if self.prev_modules is NULL:
            raise ValueError("Subinterpreter not currently active")

        cdef MyThreadState * tstate = <MyThreadState *>PyThreadState_Get()
        Py_XDECREF(tstate.interp.modules)
        Py_XDECREF(tstate.interp.modules_reloading)
        Py_XDECREF(tstate.interp.sysdict)
        Py_XDECREF(tstate.interp.builtins)
        
        tstate.interp.modules = self.prev_modules
        tstate.interp.modules_reloading = self.prev_modules_reloading
        tstate.interp.sysdict = self.prev_sysdict
        tstate.interp.builtins = self.prev_builtins
        
        #tstate.frame.f_builtins = tstate.interp.builtins
        cdef MyFrameObject * f = tstate.frame
        while f is not NULL:
            #print "<<<", <int>f
            f.f_builtins = tstate.interp.builtins
            #Py_XDECREF(tstate.interp.builtins)
            if f == f.f_back:
                f = NULL
            else:
                f = f.f_back
        
        self.prev_modules = NULL
        self.prev_modules_reloading = NULL
        self.prev_sysdict = NULL
        self.prev_builtins = NULL


