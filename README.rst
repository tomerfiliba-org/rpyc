|Version| |Python| |Tests| |License|

RPyC_ (pronounced like *are-pie-see*), or *Remote Python Call*, is a
**transparent** library for **symmetrical** `remote procedure calls`_,
clustering_, and distributed-computing_.  RPyC makes use of object-proxying_,
a technique that employs python's dynamic nature, to overcome the physical
boundaries between processes and computers, so that remote objects can be
manipulated as if they were local.

.. figure:: http://rpyc.readthedocs.org/en/latest/_images/screenshot.png
   :align: center

   A screenshot of a Windows client connecting to a Linux server.

   Note that text written to the server's ``stdout`` is actually printed on
   the server's console.


.. References:

.. _RPyC:                   https://github.com/tomerfiliba/rpyc
.. _remote procedure calls: http://en.wikipedia.org/wiki/Remote_procedure_calls
.. _clustering:             http://en.wikipedia.org/wiki/Clustering
.. _distributed-computing:  http://en.wikipedia.org/wiki/Distributed_computing
.. _object-proxying:        http://en.wikipedia.org/wiki/Proxy_pattern

.. Badges:

.. |Version| image::   https://img.shields.io/pypi/v/rpyc.svg?style=flat
   :target:            https://pypi.python.org/pypi/rpyc
   :alt:               Version

.. |Python| image::    https://img.shields.io/pypi/pyversions/rpyc.svg?style=flat
   :target:            https://pypi.python.org/pypi/rpyc#downloads
   :alt:               Python Versions

.. |Tests| image::     https://img.shields.io/travis/tomerfiliba/rpyc/master.svg?style=flat
   :target:            https://travis-ci.org/tomerfiliba/rpyc
   :alt:               Build Status

.. |License| image::   https://img.shields.io/pypi/l/rpyc.svg?style=flat
   :target:            https://github.com/tomerfiliba/rpyc/blob/master/LICENSE
   :alt:               License: MIT
