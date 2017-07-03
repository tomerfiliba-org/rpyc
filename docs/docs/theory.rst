.. _theory:

Theory of Operation
===================

This is a short outline of the "Theory of Operation" of RPyC. It will introduce the main concepts
and terminology that's required in order to understand the library's internals.

Theory
------
The most fundamental concept of computer programming, which almost all operating systems
share, is the `process <http://en.wikipedia.org/wiki/Process_(computing)>`_.
A process is a unit of code and data, contained within an `address space
<http://en.wikipedia.org/wiki/address_space>`_ -- a region of (virtual) memory,
owned solely by that process. This ensures that all processes are isolated from one another,
so that they could run on the same hardware without interfering to each other.
While this isolation is essential to operating systems and the programming model we normally use,
it also has many downsides (most of which are out of the scope of this document).
Most importantly, from RPyC's perspective, processes impose artificial boundaries between
programs which forces programs to resort to monolithic structuring.

Several mechanism exist to overcome these boundaries, most notably
`remote procedure calls <http://en.wikipedia.org/wiki/Remote_procedure_call>`_.
Largely speaking, RPCs enable one process to execute code ("call procedures") that reside
outside of its address space (in another process) and be aware of their results.
Many such RPC frameworks exist, which all share some basic traits: they provide a way to
describe what functions are exposed, define a `serialization <http://en.wikipedia.org/wiki/serialization>`_
format, transport abstraction, and a client-side library/code-generator that allows clients
utilize these remote functions.

RPyC is *yet another RPC*. However, unlike most RPCs, RPyC is **transparent**. This may sound
like a rather weird virtue at first -- but this is the key to RPyC's power: you can "plug"
RPyC into existing code at (virtually) no cost. No need to write complicated definition files,
configure name servers, set up transport (HTTP) servers, or even use special invocation
syntax -- RPyC fits the python programming model like a glove. For instance, a function that
works on a local file object will work seamlessly on a remote file object -- it's
`duck-typing <http://en.wikipedia.org/wiki/Duck_typing>`_ to the extreme.

An interesting consequence of being transparent is **symmetry** -- there's no longer a
strict notion of what's a *server* as opposed to what's a *client* -- both the parties
may serve requests and dispatch replies; the server is simply the party that accepts incoming
connections -- but other than that, servers and clients are identical.
Being symmetrical opens the doors to lots of previously unheard-of features, like
`callback functions <http://en.wikipedia.org/wiki/Callback_(computer_science)>`_.

The result of these two properties is that local and remote objects are "equal in front of
the code": your program shouldn't even be aware of the "proximity" of object it is dealing with.
In other words, two processes connected by RPyC can be thought of as a **single process**.
I like to say that RPyC *unifies the address space* of both parties, although physically,
this address space may be split between several computers.

.. note::
   The notion of address-space unification is mostly true for "classic RPyC";
   with new-style RPyC, where services dominate, the analogy is of "unifying selected parts
   of the address space".

In many situations, RPyC is employed in a master-slave relation, where the "client" takes
full control over the "server". This mainly allows the client to access remote resources
and perform operations on behalf of the server. However, RPyC can also be used as the basis
for `clustering <http://en.wikipedia.org/wiki/Cluster_(computing)>`_ and
`distributed computing <http://en.wikipedia.org/wiki/Distributed_computing>`_:
an array of RPyC servers on multiple machines can form a "huge computer" in terms of
computation power.

.. note::
   This would require some sort of framework to distribute workload and guarantee
   task completion. RPyC itself is just the mechanism.

Implementation
--------------

Boxing
^^^^^^
A major concept in the implementation of RPyC is *boxing*, which is a form of *serialization*
(encoding) that transfers objects between the two ends of the connection. Boxing relies on two
methods of serialization:

* `By Value <http://en.wikipedia.org/wiki/Evaluation_strategy#Call_by_value By>`_ -
  simple, immutable python objects (like strings, integers, tuples, etc.) are passed
  **by value**, meaning the value itself is passed to the other side. Since their value
  cannot change, there is no restriction on duplicating them on both sides.

* `By Reference <http://en.wikipedia.org/wiki/Evaluation_strategy#Call_by_reference>`_ -
  all other objects are passed **by reference**, meaning a "reference" to the object is
  passed to the other side. This allows changes applied on the referencing (proxy) object
  to be reflected on the actual object. Passing objects by reference also allows passing
  of "location-aware" objects, like files or other operating system resources.

On the other side of the connection, the process of *unboxing* takes place: by-value data is
converted ("deserialized") to local objects, while by-reference data is converted
to *object proxies*.

Object Proxying
^^^^^^^^^^^^^^^
`Object proxying <http://en.wikipedia.org/wiki/Proxy_pattern>`_ is a technique of referencing
a remote object transparently: since the remote object cannot be transferred by-value,
a reference to it is passed. This reference is then wrapped by a special object,
called a *proxy* that "looks and behaves" just like the actual object (the *target*).
Any operation performed on the proxy is delivered transparently to the target, so that
code need not be aware of whether the object is local or not.

.. note::
   RPyC uses the term ``netref`` (network reference) for a proxy object

Most of the operations performed on object proxies are *synchronous*, meaning the party that
issued the operation on the proxy waits for the operation to complete. However, sometimes
you want *asynchronous* mode of operation, especially when invoking remote functions which
might take a while to return their value. In this mode, you issue the operation and you
will later be notified of its completion, without having to block until it arrives.
RPyC supports both methods: proxy operations, are synchronous by default, but invocation
of remote functions can be made asynchronous by wrapping the proxy with an asynchronous
wrapper.

Services
^^^^^^^^
In older versions of RPyC, up to version 2.60 (now referred to as *classic RPyC*),
both parties had to "fully trust" each other and be "fully cooperative" -- there was no way
to limit the power of one party over the other. Either party could perform arbitrary
operations on the other, and there was no way to restrict it.

RPyC 3.0 introduced the concept of *services*. RPyC itself is only a "sophisticated
transport layer" -- it is a `mechanism <http://en.wikipedia.org/wiki/Separation_of_mechanism_and_policy>`_,
it does not set policies. RPyC allows each end of the connection to expose a (potentially
different) *service* that is responsible for the "policy", i.e., the set of supported operations.
For instance, *classic RPyC* is implemented by the ``SlaveService``, which grants arbitrary
access to all objects. Users of the library may define their own services, to meet their
requirements.



