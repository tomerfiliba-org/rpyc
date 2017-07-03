.. _use-cases:

Use Cases
=========

This page lists some examples for tasks that RPyC excels in solving.

Remote ("Web") Services
-----------------------
Starting with RPyC 3.00, the library is *service-oriented*. This makes implementing
**secure** remote services trivial: a service is basically a class that exposes a
well-defined set of remote functions and objects. These exposed functions can be
invoked by the clients of the service to obtain results. For example, a UPS-like company
may expose a ``TrackYourPackage`` service with ::

    get_current_location(pkgid)
    get_location_history(pkgid)
    get_delivery_status(pkgid)
    report_package_as_lost(pkgid, info)

RPyC is configured (by default) to prevent the use of ``getattr`` on remote objects to
all but "allowed attributes", and the rest of the security model is based on passing
:ref:`capabilities`. Passing capabilities is explicit and fine grained -- for instance,
instead of allowing the other party call ``open()`` and attempting to block disallowed calls
at the file-name level (which is `weak <http://en.wikipedia.org/wiki/Directory_traversal>`_),
you can pass an open file object to the other party. The other party could manipulate the
file (calling read/write/seek on it), but it would have no access to the rest of the file
system.

Administration and Central Control
----------------------------------
Efficient system administration is quite difficult: you have a variety of platforms
that you need to control, of different endianities (big/little) or bit-widths (32/64),
different administration tools, and different shell languages (``sh``, ``tcsh``,
batch files, WMI, etc.). Moreover, you have to work across numerous transport
protocols (``telnet``, ``ftp``, ``ssh``, etc.), and most system tools are domain-specific
(``awk``, ``grep``) and quite limited (operating on lines of text), and are difficult to
extend or compose together. System administration today is a mishmash of technologies.

Why not use python for that? It's a cross-platform, powerful and succinct programming
language with loads of libraries and great support. All you have to do is ``pip install rpyc``
on all of your machines, set them up to start an RPyC server on boot (over SSH or SSL),
and there you go! You can control every machine from a single place, using a unified set
of tools and libraries.

Hardware Resources
------------------
Many times you find yourself in need of utilizing hardware ("physical") resources of one
machine from another. For instance, some testgear or device can only connect to
Solaris SPARC machines, but you're comfortable with developing on your Windows workstation.
Assuming your device comes with C bindings, some command-line tool, or accepts commands
via ``ioctl`` to some `device node <http://en.wikipedia.org/wiki/Device_file>`_ --
you can just run an RPyC server on that machine, connect to it from your workstation,
and access the device programmatically with ease (using ``ctypes`` or ``popen`` remotely).


Parallel Execution
------------------
In CPython, the `GIL <http://wiki.python.org/moin/GlobalInterpreterLock>`_ prevents mutliple
threads from executing python bytecode at once. This simplifies the design of the python
interpreter, but the consequence of which is that CPython cannot utilize multiple/multicore
CPUs. The only way to achieve scalable, CPU-bound python programs is to use multiple processes,
instead of threads. The bright side of using processes over threads is reducing
synchronization problems that are inherent to multithreading -- but without a easy
way to communicate between your processes, threads are more appealing.

Using RPyC, multiprocessing becomes very easy, since we can think of RPyC-connected processes
as "one big process". Another modus operandi is having the "master" process spawn multiple
worker processes and distribute workload between them.

Distributed Computation Platform
--------------------------------

RPyC forms a powerful foundation for distributed computations and clustering: it is
architecture and platform agnostic, supports synchronous and asynchronous invocation,
and clients and servers are symmetric. On top of these features, it is easy to develop
distributed-computing frameworks; for instance, such a framework will need to:

* Take care of nodes joining or leaving the cluster
* Handle workload balancing and node failures
* Collect results from workers
* Migrate objects and code based on runtime profiling

.. note::
    RPyC itself is only a mechanism for distributed computing; it is not a distributed
    computing framework

Distributed algorithms could then be built on top of this framework to make computations faster.

Testing
-------
The first and foremost use case of RPyC is in **testing environments**, where the
concept of the library was conceived (initially as :ref:`pyinvoke <about>`).

:ref:`Classic-mode <classic>` RPyC is the ideal tool for centralized testing across multiple
machines and platforms: control your heterogeneous testing environment (simulators, devices
and other test equipment) and test procedure from the comfort of your workstation. Since RPyC
integrates so well with python, it is very easy to have your test logic run on machine A,
while the side-effects happen on machine B.

There is no need to copy and keep your files synchronized across several machines,
or work on remote file systems mounts. Also, since RPyC requires a lot of network "ping-pongs",
and because of the inherent :ref:`security risks <security>` of the *classic mode*, this mode
works best on secure, fast local networks (which is usually the case in testing environments).

