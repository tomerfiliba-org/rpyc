.. RPyC documentation master file, created by
   sphinx-quickstart on Sat May 28 10:06:21 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :hidden:
   
   tutorial
   api
   servers
   
   license
   changelog

Welcome
=======
**RPyC** (IPA: `/ɑɹ paɪ siː/ <http://en.wikipedia.org/wiki/IPA_for_English>`_, 
pronounced like *are-pie-see*), or **R**emote **Py**thon **C**all, is a **transparent**
and **symmetrical** `python <http://www.python.org >`_ library for 
`remote procedure calls <http://en.wikipedia.org/wiki/Remote_procedure_calls>`_,
`clustering <http://en.wikipedia.org/wiki/Clustering>`_ and 
`distributed-computing <http://en.wikipedia.org/wiki/Distributed_computing >`_. 
RPyC makes use of `object-proxying <http://en.wikipedia.org/wiki/Proxy_pattern>`_,
a technique that employs python's dynamic nature, to overcome the physical boundaries
between processes and computers, so that remote objects can be manipulated as if they were local. 

Features
========
* **Transparent** access to remote objects; program remotely as if working locally

* **Symmetric** protocol, where both the client and server can serve requests 
  (which allows, for instance, to use `callbacks <http://en.wikipedia.org/wiki/Callback_(computer_science)>`_

* **Synchronous** and **asynchronous** invocation

* **Platform-agnostic**: 32/64 bit, little/big endian, Windows/Linux/Solaris/Mac... 
  access objects across different architectures.

* `Capability based <http://en.wikipedia.org/wiki/Capability-based_security>`_ security model

* Integration with `TLS/SSL <http://en.wikipedia.org/wiki/Transport_Layer_Security>`_ 
  and `inetd <http://en.wikipedia.org/wiki/inetd>`_.

Use Cases
=========
* Excels in testing environments

* Control multiple hardware or software platforms from a centralized point

* Access remote physical (hardware) resources transparently

* Distribute workload among multiple machines with ease

* Implement remote services (like [wikipedia:SOAP SOAP] or [wikipedia:Java_remote_method_invocation RMI]) 
  quickly and concisely (without the overhead and limitations of these technologies)

See more [[[use cases]]].


.. Indices and tables
   ==================
    
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

