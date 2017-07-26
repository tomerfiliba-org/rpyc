.. _async:

Asynchronous Operation
======================
Many times, especially when working in a client-server model, you may want to perform
operations "in the background", i.e., send a batch of work to the server and continue
with your local operation. At some later point, you may want to poll for the completion
of the work, or perhaps be notified of its completion using a callback function.

RPyC is very well-suited for asynchronous work. In fact, the protocol itself is asynchronous,
and synchronicity is layered on top of that -- by issuing an asynchronous request and waiting
for its completion. However, since the synchronous modus-operandi is the most common one,
the library exposes a synchronous interface, and you'll need to explicitly enable
asynchronous behavior.

async()
-------
The wrapper :func:`async <rpyc.utils.helpers.async>` takes any *callable*
:ref:`netref <api-netref>` and returns an asynchronous-wrapper around that netref.
When invoked, this wrapper object dispatches the request and immediately returns an
:class:`AsyncResult <rpyc.core.async.AsyncResult>`, instead of waiting for the response.

Usage
^^^^^
Create an async wrapper around the server's ``time.sleep`` function ::

    async_sleep = rpyc.async(conn.modules.time.sleep)

And invoke it like any other function, but instead of blocking, it will immediately
return an ``AsyncResult`` ::

    res = async_sleep(5)

Which means your client can continue working normally, while the server
performs the request. There are several pitfalls using :func:`async
<pyc.utils.helpers.async>`, be sure to read the Notes_ section!

You can test for completion using ``res.ready``, wait for completion using ``res.wait()``,
and get the result using ``res.value``. You may set a timeout for the result using
``res.set_expiry()``, or even register a callback function to be invoked when the
result arrives, using ``res.add_callback()``.

Notes
^^^^^
The returns async proxies are cached by a `weak-reference <http://docs.python.org/library/weakref.html>`_.
Therefore, you must hold a strong reference to the returned proxy. Particularly, this means
that instead of doing ::

    res = async(conn.root.myfunc)(1,2,3)

Use ::

    myfunc_async = async(conn.root.myfunc)
    res = myfunc_async(1,2,3)

Furthermore, async requests provide **no guarantee on execution order**. In
particular, multiple subsequent async requests may be executed in reverse
order.


timed()
-------
:class:`timed <rpyc.utils.helpers.timed>` allows you to set a timeout for a synchronous invocation.
When a ``timed`` function is invoked, you'll synchronously wait for the result, but no longer
than the specified timeout. Should the invocation take longer, a
:class:`AsyncResultTimeout <rpyc.core.async.AsyncResultTimeout>` will be raised.

Under the hood, ``timed`` is actually implemented with ``async``: it begins dispatches the
operation, sets a timeout on the ``AsyncResult``, and waits for the response.

Example
^^^^^^^
::

    # allow this function to take up to 6 seconds
    timed_sleep = rpyc.timed(conn.modules.time.sleep, 6)

    # wait for 3 seconds -- works
    async_res = timed_sleep(3)  # returns immediately
    async_res.value             # returns after 3 seconds

    # wait for 10 seconds -- fails
    async_res = timed_sleep(10) # returns immediately
    async_res.value             # raises AsyncResultTimeout


Background Serving Thread
-------------------------
:class:`BgServingThread <rpyc.utils.helpers.BgServingThread>` is a helper class that simply starts
a background thread to serve incoming requests. Using it is quite simple::

    bgsrv = rpyc.BgServingThread(conn)
    # ...
    # now you can do blocking stuff, while incoming requests are handled in the background
    # ...
    bgsrv.stop()

Using the ``BgServingThread`` allows your code (normally the client-side) to perform blocking
calls, while still being able to process incoming request (normally from the server). This allows
the server to send "events" (i.e., invoke callbacks on the client side) while the client is busy
doing other things.

For a detailed example show-casing the ``BgServingThread``, see :ref:`tut5-events` in the
tutorial.





