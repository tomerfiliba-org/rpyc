.. _tut5:

Part 5: Asynchrounous Operation and Events
==========================================

Asynchronism
------------
The last part of the tutorial deals with a more "advanced" issue of RPC programming,
*asynchronous operation*, which is a key feature of RPyC. The code you've seen so far was
*synchronous* -- which is probably very similar to the code you normally write:
when you invoke a function, you block until the result arrives. Asynchronous invocation,
on the other hand, allows you to start the request and continue, rather than waiting.
Instead of getting the result of the call, you get a special object known as an
``AsyncResult`` (also known as a `"future" or "promise" <http://en.wikipedia.org/wiki/Futures_and_promises>`_]),
that will **eventually** hold the result.

Note that there is no guarantee on execution order for async requests!

In order to turn the invocation of a remote function (or any callable object) asynchronous,
all you have to do is wrap it with :func:`async_ <rpyc.utils.helpers.async_>`, which creates a
wrapper function that will return an ``AsyncResult`` instead of blocking. ``AsyncResult``
objects have several properties and methods that

* ``ready`` - indicates whether or not the result arrived

* ``error`` - indicates whether the result is a value or an exception

* ``expired`` - indicates whether the AsyncResult object is expired (its time-to-wait has
  elapsed before the result has arrived). Unless set by ``set_expiry``, the object will
  never expire

* ``value`` - the value contained in the AsyncResult. If the value has not yet arrived,
  accessing this property will block. If the result is an exception, accessing this property
  will raise it. If the object has expired, an exception will be raised. Otherwise, the
  value is returned

* ``wait()`` - wait for the result to arrive, or until the object is expired

* ``add_callback(func)`` - adds a callback to be invoked when the value arrives

* ``set_expiry(seconds)`` - sets the expiry time of the AsyncResult. By default, no
  expiry time is set

This may sound a bit complicated, so let's have a look at some real-life code, to convince you
it's really not that scary::

    >>> import rpyc
    >>> c=rpyc.classic.connect("localhost")
    >>> c.modules.time.sleep
    <built-in function sleep>
    >>> c.modules.time.sleep(2) # i block for two seconds, until the call returns

     # wrap the remote function with async_(), which turns the invocation asynchronous
    >>> asleep = rpyc.async_(c.modules.time.sleep)
    >>> asleep
    async_(<built-in function sleep>)

    # invoking async functions yields an AsyncResult rather than a value
    >>> res = asleep(15)
    >>> res
    <AsyncResult object (pending) at 0x0842c6bc>
    >>> res.ready
    False
    >>> res.ready
    False

    # ... after 15 seconds...
    >>> res.ready
    True
    >>> print(res.value)
    None
    >>> res
    <AsyncResult object (ready) at 0x0842c6bc>

And here's a more interesting snippet::

    >>> aint = rpyc.async_(c.builtins.int)  # async wrapper for the remote type int

    # a valid call
    >>> x = aint("8")
    >>> x
    <AsyncResult object (pending) at 0x0844992c>
    >>> x.ready
    True
    >>> x.error
    False
    >>> x.value
    8

    # and now with an exception
    >>> x = aint("this is not a valid number")
    >>> x
    <AsyncResult object (pending) at 0x0847cb0c>
    >>> x.ready
    True
    >>> x.error
    True
    >>> x.value
    Traceback (most recent call last):
    ...
      File "/opt/rpyc/rpyc/core/async_.py", line 102, in value
        raise self._obj
    ValueError: invalid literal for int() with base 10: 'this is not a valid number'

    ========= Remote Traceback (1) =========
    Traceback (most recent call last):
      File "/opt/rpyc/rpyc/core/protocol.py", line 324, in _dispatch_request
        res = self._HANDLERS[handler](self, *args)
    ...
    ValueError: invalid literal for int() with base 10: 'this is not a valid number'
    >>>

.. _tut5-events:

Events
------
Combining ``async_`` and callbacks yields a rather interesting result: *async callbacks*,
also known as **events**. Generally speaking, events are sent by an "event producer" to
notify an "event consumer" of relevant changes, and this flow is normally one-way
(from producer to consumer). In other words, in RPC terms, events can be implemented as
async callbacks, where the return value is ignored. To better illustrate the situation,
consider the following ``FileMonitor`` example -- it monitors a file
(using :func:`os.stat`) for changes, and notifies the client when a change occurs
(with the old and new ``stat`` results). ::

    import rpyc
    import os
    import time
    from threading import Thread

    class FileMonitorService(rpyc.Service):
        class exposed_FileMonitor(object):   # exposing names is not limited to methods :)
            def __init__(self, filename, callback, interval = 1):
                self.filename = filename
                self.interval = interval
                self.last_stat = None
                self.callback = rpyc.async_(callback)   # create an async callback
                self.active = True
                self.thread = Thread(target = self.work)
                self.thread.start()
            def exposed_stop(self):   # this method has to be exposed too
                self.active = False
                self.thread.join()
            def work(self):
                while self.active:
                    stat = os.stat(self.filename)
                    if self.last_stat is not None and self.last_stat != stat:
                        self.callback(self.last_stat, stat)   # notify the client of the change
                    self.last_stat = stat
                    time.sleep(self.interval)

    if __name__ == "__main__":
        from rpyc.utils.server import ThreadedServer
        ThreadedServer(FileMonitorService, port = 18871).start()


And here's a live demonstration of events::

    >>> import rpyc
    >>> f = open("/tmp/floop.bloop", "wb", buffering=0)
    >>> conn = rpyc.connect("localhost", 18871)
    >>> bgsrv = rpyc.BgServingThread(conn)  # creates a bg thread to process incoming events
    >>>
    >>> def on_file_changed(oldstat, newstat):
    ...     print("\nfile changed")
    ...     print(f"    old stat: {oldstat}")
    ...     print(f"    new stat: {newstat}")
    ...
    >>> mon = conn.root.FileMonitor("/tmp/floop.bloop", on_file_changed)  # create a filemon

    # wait a little for the filemon to have a look at the original file

    >>> f.write(b"oloop")  # change the file size and wait for filemon to notice the change
    file changed
        old stat: (33188, 1564681L, 2051L, 1, 1011, 1011, 0L, 1225204483, 1225204483, 1225204483)
        new stat: (33188, 1564681L, 2051L, 1, 1011, 1011, 6L, 1225204483, 1225204556, 1225204556)

    >>> f.close()
    >>> mon.stop()
    >>> bgsrv.stop()
    >>> conn.close()

Note that in this demo I used :class:`~rpyc.utils.helpers.BgServingThread`,
which basically starts a background thread to serve all incoming requests, while the main
thread is free to do as it wills. You don't have to open a second thread for that,
if your application has a reactor (like ``gtk``'s ``gobject.io_add_watch``): simply register
the connection with the reactor for ``read``, invoking ``conn.serve``. If you don't have a
reactor and don't wish to open threads, you should be aware that these notifications will
not be processed until you make some interaction with the connection (which pulls all
incoming requests). Here's an example of that::

    >>> conn = rpyc.connect("localhost", 18871)
    >>> mon = conn.root.FileMonitor("/tmp/floop.bloop", on_file_changed)
    >>> f.write(b"zloop")  # change the file size 

    # Notice that nothing is printed. To print the file change messages,
    # the RPyC connection must serve requests from filemon that contain stat data.
    # Dispatching a request would implicitly make the connection serve existing requests.
    # Executing conn.poll_all() would explicitly serve all requests, without an extra dispatch.
    >>> conn.poll_all()
    file changed
        old stat: (33188, 1564681L, 2051L, 1, 1011, 1011, 0L, 1225205197, 1225205197, 1225205197)
        new stat: (33188, 1564681L, 2051L, 1, 1011, 1011, 6L, 1225205197, 1225205218, 1225205218)
    >>>
