.. _use-cases:

Use Cases
=========

This page lists some tasks that RPyC can be used to solve.

Remote ("Web") Services
-----------------------
Starting with RPyC 3.00, the library is *service-oriented*. This makes implementing 
**secure** remote services trivial: a service is basically a class that exposes a 
well-defined set of remote functions and objects. These exposed functions can be 
invoked by the clients of the service to obtain results. For example, a shipping company 
may expose a {{TrackYourPackage}} service with ::

    get_current_location(pkgid)
    get_location_history(pkgid)
    get_delivery_status(pkgid)
    report_package_as_lost(pkgid, info)

RPyC is configured (by default) to prevent the use of ``getattr`` on remote objects to 
all but "allowed attributes", and the rest of the security model is based on passing 
[[[doc:capabilities]]]. Passing capabilities is explicit and fine grained -- for instance, 
you may pass a file object to another party, so it could read from/write to directly, 
but be assured that it cannot access the rest of your file system.

Administration and Central Control
----------------------------------
System administration today is hard: there's a variety of platforms you may need to control 
and the administration tools are different on each. Moreover, the utilities at hand are 
mostly domain-specific ({{grep}}, {{awk}}, ...), limited in terms of strength and 
maintainability (shell scripts, batch files), over various transport protocols 
({{telnet}}, {{rsh}}, {{ssh}}, etc.), and usually work by processing lines of text
[[footnote]]compare to [*wikipedia:Powershell][[/footnote]]. 

Instead, you can use python for your chores and gain the power of an object-oriented, 
cross-platform, library-rich programming language. Having each machine run an RPyC 
server[[footnote]]don't forget to use an authenticated server[[/footnote]] (on boot) 
allows you to control it remotely as if your scripts run on it directly. 

Hardware Resources
------------------
Many times you find yourself in need of utilizing hardware ("physical") resources of one 
machine from another. For instance, some device you may need to use comes with drivers 
only for Solaris (and the SPARC architecture), but you are more comfortable with developing 
on your Windows workstation. Assuming your device accepts commands through a 
[wikipedia:Device_file device node] ({{/dev/xxx}}) using {{ioctl}} or comes with C bindings, 
it's a no-brainer to use it through RPyC: just open the remote device node and issue 
remote {{ioclt}}s, or use the remote `ctypes <http://docs.python.org/library/ctypes.html>`_ 
module to control the device through a supplied library.

Parallel Execution
------------------
Since python threads are not able to utilize multiple CPUs, the only solution for scalable, 
CPU-bound execution is multiprocessing: running multiple python processes, which are able to 
communicate with one another (like threads). Using multiple processes instead of threads
has the benefit of solving[[footnote]]or at least reducing[[/footnote]] many of the inherent
problems with threads (namely deadlocks, races, and corruption of shared state). Using RPyC 
to achieve multiprocessing is easy, since RPyC-connected processes can be thought of as 
"sharing their address space", or as "one big process". 

Distributed Computation Platform
--------------------------------

.. note:: 
    RPyC itself is only a mechanism for distributed computing; it is not a distributed 
    computing framework

RPyC forms a powerful foundation for distributed computations and clustering: it is 
architecture and platform agnostic, supports synchronous and asynchronous invocation, 
and clients and servers are symmetric. On top of these features, it is easy to develop 
distributed-computing frameworks; for instance, such a framework will need to:

* take care of nodes joining or leaving the cluster
* handle workload balancing
* collect results from workers
* migrate objects and code based on runtime profiling

Distributed algorithms could then be built on top of this framework to make computations faster. 

Testing
-------
But the first and foremost use case of RPyC is in **testing environments**, where the 
concept of the library was conceived[[footnote]]with its predecessor, 
[[[about|PyInvoke]]][[/footnote]]. RPyC (in the [[[doc:classic mode]]]) is the ideal tool for 
centralized testing across multiple machines and platforms: control your heterogeneous 
testing environment (simulators, devices and other test equipment) and test procedure 
from the comfort of your workstation. Since RPyC integrates so well with python, it is 
very easy to have your test logic run on machine A, while the side-effects happen on 
machine B. There is no need to copy and keep your files synchronized across several machines, 
or work on remote file systems mounts[[footnote]]and on Windows it's a real problem if 
the other systems have no SMB server, which is usually the case with test equipment[[/footnote]]. 
Also, since RPyC requires a lot of network "ping-pongs", and the inherent security risks 
with the //classic mode//, it does best on secure, fast local networks (which is usually 
the case in testing environments).

