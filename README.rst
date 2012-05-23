`RPyC <http://rpyc.sourceforge.net>`_ (pronounced like *are-pie-see*), or *Remote Python Call*, 
is a **transparent** library for **symmetrical** `remote procedure calls 
<http://en.wikipedia.org/wiki/Remote_procedure_calls>`_, 
`clustering <http://en.wikipedia.org/wiki/Clustering>`_, and 
`distributed-computing <http://en.wikipedia.org/wiki/Distributed_computing>`_.
RPyC makes use of `object-proxying <http://en.wikipedia.org/wiki/Proxy_pattern>`_,
a technique that employs python's dynamic nature, to overcome the physical boundaries
between processes and computers, so that remote objects can be manipulated as if they were local.

.. figure:: http://rpyc.sourceforge.net/_static/screenshot.png
   :align: center
   
   A screenshot of a Windows client connecting to a Linux server.
   
   Note that text written to the server's ``stdout`` is actually printed on 
   the server's console.
