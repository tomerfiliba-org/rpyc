from cpython cimport PyObject, PyThreadState, PyFrameObject
from cpython cimport PyThreadState_Swap, PyThreadState_Get, Py_XINCREF, Py_XDECREF


cdef extern from "Python.h":
    PyThreadState* Py_NewInterpreter()
    void Py_EndInterpreter(PyThreadState *tstate)

ctypedef struct MyFrameObject:
    Py_ssize_t ob_refcnt
    PyObject *ob_type
    Py_ssize_t ob_size
    PyObject *f_back
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

ctypedef struct MyThreadState:
    void *next
    void *interp
    MyFrameObject *frame


cdef PyThreadState * main_interpreter = PyThreadState_Get()

cdef class SubInterpreter(object):
    cdef MyThreadState * tstate
    cdef MyThreadState * prev_tstate

    def __cinit__(self):
        cdef PyThreadState * curr
        self.tstate = NULL
        self.prev_tstate = NULL
        
        curr = PyThreadState_Get()
        self.tstate = <MyThreadState*>Py_NewInterpreter()
        PyThreadState_Swap(curr)
        
        if self.tstate is NULL:
            raise SystemError("Py_NewInterpreter failed")
    
    def __dealloc__(self):
        self.close()

    def close(self):
        cdef PyThreadState * prev
        if self.tstate is not NULL:
            prev = PyThreadState_Get()
            if prev == <PyThreadState*>self.tstate:
                prev = main_interpreter
            
            self.tstate.frame = NULL
            PyThreadState_Swap(<PyThreadState*>self.tstate)
            Py_EndInterpreter(<PyThreadState*>self.tstate)
            PyThreadState_Swap(prev)
            self.tstate = NULL
            self.prev_tstate = NULL

    def __enter__(self):
        if self.prev_tstate is not NULL:
            raise ValueError("Subinterpreter already active")
        
        self.prev_tstate = <MyThreadState*>PyThreadState_Get()
        PyThreadState_Swap(<PyThreadState*>self.tstate)
        self.prev_tstate.frame.f_tstate = self.tstate
        self.tstate.frame = self.prev_tstate.frame
        self.prev_tstate.frame = NULL
        return self

    def __exit__(self, t, v, tb):
        if self.prev_tstate is NULL:
            raise ValueError("Subinterpreter not currently active")

        PyThreadState_Swap(<PyThreadState*>self.prev_tstate)
        self.prev_tstate.frame = self.tstate.frame
        self.tstate.frame = NULL

        self.prev_tstate.frame.f_tstate = self.prev_tstate
        Py_XDECREF(self.prev_tstate.frame.f_exc_type)
        Py_XDECREF(self.prev_tstate.frame.f_exc_value)
        Py_XDECREF(self.prev_tstate.frame.f_exc_traceback)
        self.prev_tstate.frame.f_exc_type = <PyObject*>t
        self.prev_tstate.frame.f_exc_value = <PyObject*>v
        self.prev_tstate.frame.f_exc_traceback = <PyObject*>tb
        Py_XINCREF(self.prev_tstate.frame.f_exc_type)
        Py_XINCREF(self.prev_tstate.frame.f_exc_value)
        Py_XINCREF(self.prev_tstate.frame.f_exc_traceback)
        
        self.prev_tstate = NULL




