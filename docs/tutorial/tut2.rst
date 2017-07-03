.. _tut2:

Part 2: Code Samples
====================

In this part, we'll dive deeper into the classic mode by analyzing some more code samples.

Setup
-----
Creating a connection and accessing modules ::

    >>> import rpyc
    >>> conn = rpyc.classic.connect("localhost")
    >>> conn
    <rpyc.core.protocol.Protocol object at 0x00B9F830>
    >>> conn.modules
    <rpyc.services.slave.ModuleNamespace object at 0x00B77DA0>

    >>> conn.modules.sys
    <module 'sys' (built-in)>
    >>> conn.modules.os
    <module 'os' from 'C:\Python25\lib\os.pyc'>
    >>> conn.modules.telnetlib
    <module 'telnetlib' from 'C:\Python25\lib\telnetlib.pyc'>
    >>> conn.modules["xml.dom.minidom"]
    <module 'xml.dom.minidom' from 'C:\Python25\lib\xml\dom\minidom.pyc'>

Basic usage
-----------
Working with remote objects ::

    >>> conn.modules.sys.path
    ['D:\\projects\\rpyc\\servers', 'd:\\projects', .....]
    >>> conn.modules.sys.path.append("regina victoria")
    >>> conn.modules.sys.path
    ['D:\\projects\\rpyc\\servers', 'd:\\projects', ....., 'regina victoria']

    >>> conn.modules.sys.stdout
    <open file '<stdout>', mode 'w' at 0x0098F068>
    >>> conn.modules.sys.stdout.write("hello world\n")
    # 'hello world' is printed on the server

    >>> conn.modules.os.path.abspath("lalala")
    'D:\\eclipse\\lalala'
    [[/code]]

    Experimenting with remote objects:
    [[code type="python"]]
    >>> conn.modules.sys.path[0]
    'D:\\projects\\rpyc\\servers'
    >>> conn.modules.sys.path[1]
    'd:\\projects'
    >>> conn.modules.sys.path[3:6]
    ['C:\\Python25\\DLLs', 'C:\\Python25\\lib', 'C:\\Python25\\lib\\plat-win']
    >>> len(conn.modules.sys.path)
    12
    >>> for i in conn.modules.sys.path:
    ...     print i
    ...
    D:\projects\rpyc\servers
    d:\projects
    C:\WINDOWS\system32\python25.zip
    C:\Python25\DLLs
    C:\Python25\lib
    C:\Python25\lib\plat-win
    C:\Python25\lib\lib-tk
    C:\Python25
    C:\Python25\lib\site-packages
    C:\Python25\lib\site-packages\gtk-2.0
    C:\Python25\lib\site-packages\wx-2.8-msw-unicode
    regina victoria

Introspection
-------------
So far everything seemed normal. Now it's time to get our hands dirty and figure out what
exactly are these magical objects... ::

    >>> type(conn.modules.sys.path)
    <netref class '__builtin__.list'>
    >>> type(conn.modules.sys.stdout)
    <netref class '__builtin__.file'>
    >>> type(conn.modules.os.listdir)
    <netref class '__builtin__.builtin_function_or_method'>
    >>> type(conn.modules.os.path.abspath)
    <netref class '__builtin__.function'>

Voila, **netrefs** (*network references*, also known as *transparent object proxies*) are
special objects that delegate everything done on them locally to the corresponding remote
objects. Netrefs may not be real lists of functions or modules, but they "do their best"
to look and feel like the objects they point to... in fact, they even fool python's
introspection mechanisms! ::

    >>> isinstance(conn.modules.sys.path, list)
    True
    >>> import inspect
    >>> inspect.isbuiltin(conn.modules.os.listdir)
    True
    >>> inspect.isfunction(conn.modules.os.path.abspath)
    True
    >>> inspect.ismethod(conn.modules.os.path.abspath)
    False
    >>> inspect.ismethod(conn.modules.sys.stdout.write)
    True
    >>> dir(conn.modules.sys.path)
    ['____conn__', '____oid__', '__add__', '__class__', '__contains__', '__delattr__',
    '__delitem__', '__delslice__', '__doc__', '__eq__', '__ge__', '__getattribute__',
    '__getitem__', '__getslice__', '__gt__', '__hash__', '__iadd__', '__imul__',
    '__init__', '__iter__', '__le__', '__len__', '__lt__', '__mul__', '__ne__', '__new__',
    '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', '__setattr__',
    '__setitem__', '__setslice__', '__str__', 'append', 'count', 'extend', 'index', 'insert',
    'pop', 'remove', 'reverse', 'sort']

Exceptions
----------
But things are not always bright, and exceptions must be dealt with. When a client makes a
request that fails (an exception is raised on the server side), the exception propagates
transparently to the client. Have a look at this snippet::

    >>> conn.modules.sys.path[300]         # there are only 12 elements in the list...
    ======= Remote traceback =======
    Traceback (most recent call last):
      File "D:\projects\rpyc\core\protocol.py", line 164, in _dispatch_request
        res = self._handlers[handler](self, *args)
      File "D:\projects\rpyc\core\protocol.py", line 321, in _handle_callattr
        return attr(*args, **dict(kwargs))
    IndexError: list index out of range

    ======= Local exception ========
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "D:\projects\rpyc\core\netref.py", line 86, in method
        return self.____sync_req__(consts.HANDLE_CALLATTR, name, args, kwargs)
      File "D:\projects\rpyc\core\netref.py", line 53, in ____sync_req__
        return self.____conn__.sync_request(handler, self.____oid__, *args)
      File "D:\projects\rpyc\core\protocol.py", line 224, in sync_request
        self.serve()
      File "D:\projects\rpyc\core\protocol.py", line 196, in serve
        self._serve(msg, seq, args)
      File "D:\projects\rpyc\core\protocol.py", line 189, in _serve
        self._dispatch_exception(seq, args)
      File "D:\projects\rpyc\core\protocol.py", line 182, in _dispatch_exception
        raise obj
    IndexError: list index out of range
    >>>

As you can see, we get two tracebacks: the remote one, showing what went wrong on the server,
and a local one, showing what we did to cause it.

Misc
----
Aside from the very useful ``.modules`` attribute of ``conn``, classic RPyC provides
some more useful entry points:

* ``builtins`` - the ``__builtin__`` module (short for ``conn.modules.__builin__``)
* ``eval(expr : str)`` - evaluates the expression on the server (a remote ``eval`` function)
* ``execute(code : str)`` - executes the code on the server (a remote ``exec`` statement)
* ``namespace`` - a per-connection ``dict`` in which code is executed and evaluated (
  (by the ``execute`` and ``eval`` methods)

Here are some examples ::

    >>> remlist = conn.builtin.range(50)
    >>> conn.execute("print 'world'")      # 'world' is printed on the server
    >>> conn.execute("x = 7")              # a variable named 'x' is defined on the server
    >>> conn.namespace["x"]
    7
    >>> conn.eval("x + 6")                 # this code is evaluated on the server
    13



Continue to :ref:`part 3 <tut3>`...

