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
that's exposed by the other party. For security concerns, only access is only granted to
``exposed_`` members. For instance, the ``foo`` method above is inaccessible (attempting to
call it will result in an ``AttributeError``).

RPyC is a symmetric protocol, which means both ends of the connection can act as clients
or servers


ALIASES
on_connect(self)
on_disconnect(self)


Symmetry
--------


Built-in Services
-----------------
RPyC comes bundled with two basic services:
* :class:`VoidService <rpyc.core.service.VoidService>`, which is an empty "do-nothing" 
  service. It's useful when you want only one side of the connection to provide a service,
  while the other side a "consumer".
* :class:`SlaveService <rpyc.core.service.SlaveService>`, which



Configuration Parameters
------------------------

Attribute Access
----------------

_rpyc_getattr(self, name)
_rpyc_delattr(self, name)
_rpyc_setattr(self, name, value)



