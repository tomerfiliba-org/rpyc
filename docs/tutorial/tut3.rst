.. _tut3:

Part 3: Services and *New Style* RPyC
=====================================

So far we have covered the features of classic RPyC. However, the new model of RPyC
programming (starting with RPyC 3.00), is based on *services*. As you might have noticed
in the classic mode, the client basically gets full control over the server, which is
why we (used to) call RPyC servers *slaves*. Luckily, this is no longer the case.
The new model is *service oriented*: services provide a way to expose a well-defined set
of capabilities to the other party, which makes RPyC a generic RPC platform. In fact, the
*classic RPyC* that you've seen so far, is simply "yet another" service.

Services are quite simple really. To prove that, the ``SlaveService`` (the service that
implements classic RPyC) is only 30 lines long, including comments ;). Basically, a service
has the following boilerplate::

    import rpyc

    class MyService(rpyc.Service):
        def on_connect(self, conn):
            # code that runs when a connection is created
            # (to init the service, if needed)
            pass

        def on_disconnect(self, conn):
            # code that runs after the connection has already closed
            # (to finalize the service, if needed)
            pass

        def exposed_get_answer(self): # this is an exposed method
            return 42

        exposed_the_real_answer_though = 43     # an exposed attribute

        def get_question(self):  # while this method is not exposed
            return "what is the airspeed velocity of an unladen swallow?"

.. note::
    The ``conn`` argument for ``on_connect`` and ``on_disconnect`` are added
    in rpyc 4.0. This is backwards incompatible with previous versions where
    instead the service constructor is called with a connection parameter and
    stores it into ``self._conn``.

As you can see, apart from the special initialization/finalization methods, you are free
to define the class like any other class. Unlike regular classes, however, you can
choose which attributes will be exposed to the other party: if the name starts
with ``exposed_``, the attribute will be remotely accessible, otherwise it is only
locally accessible. In this example, clients will be able to call ``get_answer``,
but not ``get_question``, as we'll see in a moment.

To expose your service to the world, however, you will need to start a server. There are many
ways to do that, but the simplest is ::

    # ... continuing the code snippet from above ...

    if __name__ == "__main__":
        from rpyc.utils.server import ThreadedServer
        t = ThreadedServer(MyService, port=18861)
        t.start()

To the remote party, the service is exposed as the root object of the connection, e.g.,
``conn.root``. Now you know all you need to understand this short demo:

    >>> import rpyc
    >>> c = rpyc.connect("localhost", 18861)
    >>> c.root
    <__main__.MyService object at 0x834e1ac>

This "root object" is a reference (netref) to the service instance living in the
server process. It can be used access and invoke exposed attributes and methods:

    >>> c.root.get_answer()
    42
    >>> c.root.the_real_answer_though
    43

Meanwhile, the question is not exposed:

    >>> c.root.get_question()
    ======= Remote traceback =======
    ...
      File "/home/tomer/workspace/rpyc/core/protocol.py", line 298, in sync_request
        raise obj
    AttributeError: cannot access 'get_question'


Access policy
-------------
By default methods and attributes are only visible if they start with the
``exposed_`` prefix. This also means that attributes of builtin objects such
as lists or dicts are not accessible by default. If needed, you can configure
this by passing appropriate options when creating the server. For example::

    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(MyService, port=18861, protocol_config={
        'allow_public_attrs': True,
    })
    server.start()

For a description of all available settings see the
:data:`~rpyc.core.protocol.DEFAULT_CONFIG`.


Shared service instance
-----------------------
Note that we have here passed the *class* ``MyService`` to the server with the
effect that every incoming connection will use its own, independent
``MyService`` instance as root object.

If you pass in an *instance* instead, all incoming connections will use this
instance as their shared root object, e.g.::

        t = ThreadedServer(MyService(), port=18861)

Note the subtle difference (parentheses!) to the example above.

.. note::
    Passing instances is supported starting with rpyc 4.0. In earlier
    versions, you can only pass a class of which every connection will receive
    a separate instance.


Passing arguments to the service
--------------------------------
In the second case where you pass in a fully constructed service instance, it
is trivial to pass additional arguments to the ``__init__`` function. However,
the situation is slightly more tricky if you want to pass arguments while
separating the root objects for each connection. In this case, use
:func:`~rpyc.utils.helpers.classpartial` like so::

        from rpyc.utils.helpers import classpartial

        service = classpartial(MyService, 1, 2, pi=3)
        t = ThreadedServer(service, port=18861)

.. note::
    classpartial is added in version 4.0.


But Wait, There's More!
-----------------------
All services have a *name*, which is normally the name of the class, minus the
``"Service"`` suffix. In our case, the service name is ``"MY"`` (service names are
case-insensitive). If you wish to define a custom name, or multiple names (aliases),
you can do so by setting the ``ALIASES`` list. The first alias is considered to be the
"formal name", while the rest are aliases::

    class SomeOtherService(rpyc.Service):
        ALIASES = ["floop", "bloop"]
        ...

In the original code snippet, this is what the client gets::

    >>> c.root.get_service_name()
    'MY'
    >>> c.root.get_service_aliases()
    ('MY',)

The reason services have names is for the **service registry**: normally, a server will
broadcast its details to a nearby :ref:`registry server <registry-server>` for discovery.
To use service discovery, a make sure you start the ``bin/rpyc_registry.py``.
This server listens on a broadcast UDP socket, and will
answer to queries about  which services are running where.

Once a registry server is running somewhere "broadcastable" on your network, and the
servers are configured to auto-register with it (the default), clients can discover
services *automagically*. To find servers running a given service name::

    >>> rpyc.discover("MY")
    (('192.168.1.101', 18861),)

And if you don't care to which you server you connect, you use connect_by_service:

    >>> c2 = rpyc.connect_by_service("MY")
    >>> c2.root.get_answer()
    42

Decoupled Services
------------------
So far we've discussed only about the service that the **server** exposes, but what about
the client? Does the client expose a service too? After all, RPyC is a symmetric protocol --
there's no difference between the client and the server. Well, as you might have guessed,
the answer is yes: both client and server expose services. However, the services exposed
by the two parties need not be the same -- they are **decoupled**.

By default, clients (using one of the ``connect()`` functions to connect to a server)
expose the ``VoidService``. As the name suggests, this service exposes no functionality to the
other party, meaning the server can't make requests to the client (except for explicitly
passed capabilities, like function callbacks). You can set the service exposed by the client
by passing the ``service =`` parameter to one of the :func:`~rpyc.utils.factory.connect`
functions.

The fact that the services on both ends of the connection are decoupled, does not mean
they can be arbitrary. For instance, "service A" might expect to be connected to "service B" --
and runtime errors (mostly ``AttributeError``) will ensue if this not the case. Many times the
services on both ends can be different, but do keep it in mind that if you need interaction
between the parties, both services must be "compatible".

.. note::
   **Classic mode:** when using any of the :func:`~rpyc.utils.classic.connect` functions,
   the client-side service is set to ``SlaveService`` as well (being identical to the server).


Continue to :ref:`tut4`...
