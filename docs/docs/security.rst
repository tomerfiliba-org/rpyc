.. _security:

Security
========
Operating over a network always involve a certain security risk, and requires some awareness.
Version 3 of RPyC was a rewrite of the library, specifically targeting security and
service-orientation. Unlike version 2.6, RPyC no longer makes use of insecure protocols like ``pickle``,
supports :data:`security-related configuration parameters <rpyc.core.protocol.DEFAULT_CONFIG>`,
comes with strict defaults, and encourages the use of a capability-based security model. Even so, it behooves you to
take a layered to secure programming and not let RPyC be a single point of failure.

`CVE-2019-16328`_ is the first vulnerability since 2008, which made it possible for a remote attacker to
bypass standard protocol security checks and modify the behavior of a service. The latent flaw was committed
to master from September 2018 to October 2019 and affected versions `4.1.0` and `4.1.1`. As of version
`4.1.2`, the vulnerability has been fixed.

RPyC is intuitive and secure when used properly. However, if not used properly, RPyC is also the perfect back-door...
The general recommendation is not to use RPyC openly exposed over the Internet. It's wiser to use it only over secure local
networks, where you trust your peers. This does not imply that there's anything wrong with the
mechanism--but the implementation details are sometimes too subtle to be sure of.
Of course, you can use RPyC over a :ref:`secure connection <ssl>`, to mitigate these risks.

RPyC works by exposing a root object, which in turn may expose other objects (and so on). For
instance, if you expose a module or an object that has a reference to the ``sys`` module,
a user may be able to reach it. After reaching ``sys``, the user can traverse ``sys.modules`` and
gain access to all of the modules that the server imports. More complex methodologies, similar to those used in ``CVE-2019-16328``,
could leverage access to ``builtins.str``, ``builtins.type``, ``builtins.object``, and ``builtins.dict`` and gain access to
``sys`` modules. The default configurations for RPyC are intended to mitigate access to dangerous objects. But if you enable
``allow_public_attrs``, return uninitialized classes or override ``_rpyc_getattr`` such things are likely to slip under the radar
(it's possible to prevent this -- see below).

.. _CVE-2019-16328: https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-16328


Wrapping
--------
The recommended way to avoid over-exposing of objects is *wrapping*. For example, if your object
has the attributes ``foo``, ``bar``, and ``spam``, and you wish to restrict access to ``foo`` and
``bar`` alone -- you can do ::

    class MyWrapper(object):
        def __init__(self, obj):
            self.foo = obj.foo
            self.bar = obj.bar

Since this is a common idiom, RPyC provides :func:`~rpyc.utils.helpers.restricted`.
This function returns a "restricted view" of the given object, limiting access only to the
explicitly given set of attributes. ::

    class MyService(rpyc.Service):
        def exposed_open(self, filename):
            f = open(filename, "r")
            return restricted(f, ["read", "close"], [])  # allow access only to 'read' and 'close'

Assuming RPyC is configured to allow access only to safe attributes (the default), this would
be secure.

When exposing modules, you can use the ``__all__`` list as your set of accessible attributes --
but do keep in mind that this list may be unsafe.

Classic Mode
------------
The classic mode (``SlaveService``) is **intentionally insecure** -- in this mode, the server
"gives up" on security and exposes everything to the client. This is especially useful for testing
environments where you basically want your client to have full control over the server. Only ever use
a classic mode server over secure local networks.

.. _config-params-security:

Configuration Parameters
------------------------
By default, RPyC is configured to allow very little attribute access. This is useful when your
clients are untrusted, but this may be a little too restrictive. If you get "strange"
``AttributeError`` exceptions, stating that access to certain attributes is denied -- you may
need to tweak the configuration parameters. Normally, users tend to enable ``allow_public_attrs``,
but, as stated above, this may have undesired implications.

Attribute Access
----------------
RPyC has a rather elaborate attribute access scheme, which is controlled by configuration
parameters. However, in case you need more fine-grained control, or wish to completely override
the configuration for some type of objects -- you can implement the **RPyC attribute protocol**.
This protocol consists of ``_rpyc_getattr``, ``_rpyc_setattr``, and ``_rpyc_delattr``, which
are parallel to ``__getattr__`` / ``__setattr__`` / ``__delattr__``. Their signatures are ::

    _rpyc_getattr(self, name)
    _rpyc_delattr(self, name)
    _rpyc_setattr(self, name, value)

Any object that implements this protocol (or part of it) will override the default attribute
access policy. For example, if you generally wish to disallow access to protected attributes,
but have to expose a certain protected attribute of some object, just define ``_rpyc_getattr``
for that object which allows it::

    class MyObjectThatExposesProtectedAttrs(object):
        def __init__(self):
            self._secret = 18
        def _rpyc_getattr(self, name):
            if name.startswith("__"):
                # disallow special and private attributes
                raise AttributeError("cannot accept private/special names")
            # allow all other attributes
            return getattr(self, name)








