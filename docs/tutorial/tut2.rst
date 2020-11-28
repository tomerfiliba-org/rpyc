.. _tut2:

Part 2: Netrefs and Exceptions
==============================

In :ref:`tut1`, we have seen how to use rpyc classic connection to do almost
anything remotely.

So far everything seemed normal. Now it's time to get our hands dirty and
understand more what happens under the hood!

Setup
-----
Start a classic server using::

    python bin/rpyc_classic.py

And connect your client::

    >>> import rpyc
    >>> conn = rpyc.classic.connect("localhost")


Netrefs
-------

We know that we can use ``conn.modules.sys`` to access the ``sys`` module the
server… But what kind of magical object is that thing anyway?

    >>> type(conn.modules.sys)
    <netref class 'builtins.module'>

    >>> type(conn.modules.sys.path)
    <netref class 'builtins.list'>

    >>> type(conn.modules.os.path.abspath)
    <netref class 'builtins.function'>

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

Cool, eh?

We all know that the best way to understand something is to smash it, slice it
up and spill the contents into the world! So let's do that::

    >>> dir(conn.modules.sys.path)
    ['____conn__', '____id_pack__', '__add__', '__class__', '__contains__', '__delattr__',
    '__delitem__', '__delslice__', '__doc__', '__eq__', '__ge__', '__getattribute__',
    '__getitem__', '__getslice__', '__gt__', '__hash__', '__iadd__', '__imul__',
    '__init__', '__iter__', '__le__', '__len__', '__lt__', '__mul__', '__ne__', '__new__',
    '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', '__setattr__',
    '__setitem__', '__setslice__', '__str__', 'append', 'count', 'extend', 'index', 'insert',
    'pop', 'remove', 'reverse', 'sort']

In addition to some expected methods and properties, you will have noticed
``____conn__`` and ``____id_pack__``. These properties store over which connection
the object should be resolved and an identifier that allows the server to
lookup the object from a dictionary.

Exceptions
----------
Let's continue on this exhilarating path of destruction. After all, things are
not always bright, and problems must be dealt with. When a client makes a
request that fails (an exception is raised on the server side), the exception
propagates transparently to the client. Have a look at this snippet::

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
        return self.____conn__.sync_request(handler, self.____id_pack__, *args)
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


Custom Exception Handling Example
---------------------------------
The server example::

    import rpyc
    import urllib.error
    from rpyc.utils.server import OneShotServer


    class HelloService(rpyc.Service):
        def exposed_foobar(self, remote_str):
            raise urllib.error.URLError("test")


    if __name__ == "__main__":
        rpyc.lib.setup_logger()
        server = OneShotServer(
            HelloService,
            port=12345,
            protocol_config={'import_custom_exceptions': True}
        )
        server.start()


The client example::

    import rpyc
    import urllib.error
    rpyc.core.vinegar._generic_exceptions_cache["urllib.error.URLError"] = urllib.error.URLError


    if __name__ == "__main__":
        conn = rpyc.connect("localhost", 12345)
        try:
            print(conn.root.foobar('hello'))
        except urllib.error.URLError:
            print('caught a URLError')


Continue to :ref:`tut3`...
