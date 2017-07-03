.. _services:

Services
========

RPyC is oriented around the notion of :ref:`services <api-service>`. Services are classes that
derive from :class:`rpyc.core.service.Service` and define "exposed methods" -- normally, methods
whose name explicitly begins with ``exposed_``. Services also have a name, or a list of aliases.
Normally, the name of the service is the name of its class (excluding a possible ``Service``
suffix), but you can override this behavior by specifying the ``ALIASES`` attribute in the class.

Let's have a look at a rather basic service -- a calculator
(see :ref:`custom-servers` for more info) ::

    import rpyc

    class CalculatorService(rpyc.Service):
        def exposed_add(self, a, b):
            return a + b
        def exposed_sub(self, a, b):
            return a - b
        def exposed_mul(self, a, b):
            return a * b
        def exposed_div(self, a, b):
            return a / b
        def foo(self):
            print "foo"

When a client connects, it can access any of the exposed members of the service ::

    import rpyc

    conn = rpyc.connect("hostname", 12345)
    x = conn.root.add(4,7)
    assert x == 11

    try:
        conn.root.div(4,0)
    except ZeroDivisionError:
        pass

As you can see, the ``root`` attribute of the connection gives you access to the service
that's exposed by the other party. For security concerns, access is only granted to
``exposed_`` members. For instance, the ``foo`` method above is inaccessible (attempting to
call it will result in an ``AttributeError``).

Implementing Services
---------------------
As previously explained, all ``exposed_`` members of your service class will be available to
the other party. This applies to methods, but in fact, it applies to any attribute. For instance,
you may expose a class::

    class MyService(rpyc.Service):
        class exposed_MyClass(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b
            def exposed_foo(self):
                return self.a + self.b

If you wish to change the name of your service, or specify a list of aliases, set the ``ALIASES``
(class-level) attribute to a list of names. For instance::

    class MyService(rpyc.Service):
        ALIASES = ["foo", "bar", "spam"]

The first name in this list is considered the "proper name" of the service, while the rest
are considered aliases. This distinction is meaningless to the protocol and the registry server.

Your service class may also define two special methods: ``on_connect(self)`` and
``on_disconnect(self)``. These methods are invoked, not surprisingly, when a connection
has been established, and when it's been disconnected. Note that during ``on_disconnect``,
the connection is already dead, so you can no longer access any remote objects.

Other than that, your service instance has the ``_conn`` attribute, which represents the
:class:`connection <rpyc.core.protocol.Connection>` that it serves. This attribute already
exists when ``on_connected`` is called.

.. note::
   Try to avoid overriding the ``__init__`` method of the service. Place all initialization-related
   code in ``on_connect``.

Built-in Services
-----------------
RPyC comes bundled with two built-in services:

* :class:`VoidService <rpyc.core.service.VoidService>`, which is an empty "do-nothing"
  service. It's useful when you want only one side of the connection to provide a service,
  while the other side a "consumer".

* :class:`SlaveService <rpyc.core.service.SlaveService>`, which implements
  :ref:`Classic Mode<classic>` RPyC.

Decoupled Services
------------------
RPyC is a symmetric protocol, which means both ends of the connection can act as clients
or servers -- in other words -- both ends may expose (possibly different) services. Normally,
only the server exposes a service, while the client exposes the ``VoidService``, but this is
not constrained in any way. For instance, in the classic mode, both ends expose the
``SlaveService``; this allows each party to execute arbitrary code on its peer. Although
it's not the most common use case, two-sides services are quite useful. Consider this client::

    class ClientService(rpyc.Service):
        def exposed_foo(self):
            return "foo"

    conn = rpyc.connect("hostname", 12345, service = ClientService)

And this server::

    class ServerService(rpyc.Service):
        def exposed_bar(self):
            return self._conn.root.foo() + "bar"

The client can invoke ``conn.root.bar()`` on the server, which will, in turn, invoke ``foo`` back
on the client. The final result would be ``"foobar"``.

Another approach is to pass **callback functions**. Consider this server::

    class ServerService(rpyc.Service):
        def exposed_bar(self, func):
            return func() + "bar"

And this client::

    def foofunc():
        return "foo"

    conn = rpyc.connect("hostname", 12345)
    conn.root.bar(foofunc)


See also :ref:`config-params-security`

