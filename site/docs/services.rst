.. _services:

Services
========

RPyC is oriented around the notion of :ref:`services <api-service>`. Services are classes that
derive from :class:`rpyc.core.service.Service` and define "exposed methods" -- normally, methods
whose name explicitly begins with ``exposed_``. Services also have a name, or a list of aliases.
Normally, the name of the service is the name of its class (excluding a possile ``Service`` 
suffix), but you can override this behavior

For instance, a Calculator service may look 
like so (see :ref:`custom-servers` for more info) ::

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

When a client connects,  



VoidService

SlaveService


