.. _theory:

Theory of Operation
===================

This is a short outline of the "Theory of Operation" of RPyC. It will introduce the main concepts
and terminology that's required in order to understand the library's internals.

Theory
------
The most fundamental concept of computer programming, which almost all operating systems
share, is the `process <wikipedia:Process_(computing)>`_. A process is a unit of code and data, 
contained within an [wikipedia:address_space address space] -- a region of (virtual) memory 
owned solely by that process. This ensures that all processes are isolated from one another, 
so that they could run on the same hardware without interfering to each other. 
While the concept of processes is essential in today's architecture, it also has many 
downsides (most of which are out of the scope of this document). Most importantly from RPyC's 
perspective, processes imposes artificial boundaries between programs and most programs resort 
to monolithic structuring.

However, several mechanism exist to overcome these boundaries, most notably 
`RPCs <wikipedia:Remote_procedure_call>` (remote procedure calls). Largely speaking, RPCs 
enable one process to execute code (call functions) that reside outside of its address space
(another process) and be aware of side effects (return values). Many such RPCs exist, I 
daresay //too many//[[footnote]]See my article 
[http://tomeronsoftware.wikidot.com/blog:everything-is-rpc "Everything is RPC"][[/footnote]], 
but basically they are all the same: they provide a way to describe what functions are exposed 
(usually by the form of a [wikipedia:Domain-specific_language DSL]), define a 
[wikipedia:serialization] format, a security model and transports, and a client-side 
library/auto-generated code that allows clients utilize the remote functions.


RPyC is //yet another RPC//. However, unlike most RPCs, RPyC is **transparent**. This may sound
like a rather weird virtue at first -- but this is the key to RPyC's power: you can "plug" 
RPyC into existing code at (virtually) no cost. No need to write complicated definition files,
configure name servers, set up transport (HTTP) servers, or even use special invocation 
syntax -- RPyC fits the python programming model like a glove. For instance, a function that 
works on a local file object will work seamlessly on a remote file object -- it's utilizing 
[wikipedia:Duck_typing duck-typing] to its full potential.

An interesting consequence of being transparent is **symmetry**, meaning, the traditional 
roles of "server" and "client" are quite ambiguous. In other words, both the server and 
the client may serve requests and dispatch replies; the server is simply the party that
accepts connections. Being symmetrical allows both parties to execute code remotely, 
such as passing [wikipedia:Callback_(computer_science) callback functions] to one another.

The result of these two properties is that local and remote objects are "equal in front of 
the code": your program shouldn't even be aware of what kind of object it is dealing with.
In other words, two processes connected by RPyC can be thought of as a **single process**. 
We say that RPyC **unifies the address space** of its connected parties, although physically, 
it may be split between several computers[[footnote]]This address-space unification is mostly 
true for "classic RPyC"; with new-style RPyC (services), the analogy is "selected parts of 
the address space are unified"[[/footnote]]. 

In many situations, RPyC is employed in a master-slave relation, where the "client" takes
full control over the "server". This mainly allows the client to access remote resources 
and perform operations on behalf of the server. However, RPyC can also be used as the basis
for [wikipedia:Cluster_(computing) clustering] and 
[wikipedia:Distributed_computing distributed computing]: an array of RPyC servers on 
multiple machines can form a "huge computer" in terms of computation power[[footnote]]
Requires some sort of framework to distribute workload and guarantee task completion. 
RPyC itself is just the mechanism.[[/footnote]].

Implementation
--------------
Boxing
^^^^^^
A major concept in the implementation of RPyC is *boxing*, which is a form of 
[wikipedia:serialization] ("encoding") that transfers objects between the two ends of the 
connection. Boxing relies on two methods of serialization:

* [wikipedia:Evaluation_strategy#Call_by_value By Value] - simple, immutable python objects 
  (like strings, integers, tuples, etc.) are passed **by value**, meaning the value itself is 
  passed to the other side. Since their value cannot change, there is no restriction on copying
  them. Their value is serialized 

* [wikipedia:Evaluation_strategy#Call_by_reference By Reference] - all other objects are 
  passed **by reference**, meaning a "reference" to the object is passed to the other side.
  This allows changes applied on the referenced object to be reflected on the actual object.
  Passing objects by reference also allows passing of "location-aware" objects, like files 
  and other operating system resources.

On the other side of the connection, the process of *unboxing* takes place: by-value data is
converted ("deserialized") to local objects, while by-reference data is converted 
to *object proxies*.

Object Proxying
^^^^^^^^^^^^^^^
`Object proxying <wikipedia:Proxy_pattern>`_ is a technique of referencing a remote object 
transparently: since the remote object cannot be transferred by-value, a reference to it is 
passed. This reference is then wrapped by a special object, called a **proxy**[[footnote]]
RPyC uses the term {{Netref}} -- network reference[[/footnote]], that "looks and behaves" 
just like the actual object (the //target//). Any operation performed on the proxy is 
delivered transparently to the target, so that code need not be aware of whether the object
is local or not.

Most of the operations performed on object proxies are synchronous, meaning the party that 
issued the operation on the proxy waits for the operation to complete. Many times, however,
especially in the invocation of remote functions, it is desired to perform asynchronous
operations: issue the operation and be notified of its completion without waiting. 
RPyC supports both methods: proxy operations, by default, are synchronous, but proxy invocation
can be made asynchronous by wrapping the proxy with a special wrapper object.

Services
^^^^^^^^
In older versions of RPyC[[footnote]]what is now called "classic RPyC"[[/footnote]], 
up until version 2.60, all RPyC parties where "fully cooperative" or "slaves": 
either party could perform arbitrary operations on the other. There was no way to restrict or 
define a subset of what one party could perform on another.

RPyC 3.00 introduced the concept of **services**. RPyC itself is only a sophisticated 
transport layer -- it is a [wikipedia:Separation_of_mechanism_and_policy mechanism], 
it does not set policies. Each end of the RPyC connection has an attached service 
(also called {{root}}), that is responsible for the "policy" (the set of allowed operations). 
For instance, "Classic RPyC" is implemented as the {{SlaveService}}, which allows arbitrary 
access to all objects. Custom services, however, can define a set of allowed operations, 
as suitable for your needs.



