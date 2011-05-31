.. _install:

Download and Install
====================

.. toctree::
   :hidden:

   changelog

You can always download the latest releases of RPyC from the project's 
`sourceforge page <http://sourceforge.net/projects/rpyc/files/main>`_ or the 
its `PyPI page <http://pypi.python.org/pypi/RPyC>`_. RPyC is distributed as a 
``zip``, a ``tar.gz``, and a win32 installer. Of course you can also use 
``easy_install rpyc`` and ``pip install rpyc`` just as well.

You may also wish to read the :ref:`change log <changelog>` before installing 
new versions.

Platforms and Interpreters
--------------------------
RPyC is a pure-python library, and as such can run on any architecture and 
platform that runs python (or one of its other implementations), both 32- 
and 64-bit. This is also true for a client and its server, which may run on
different architectures. The latest release supports:

* Python (CPython) 2.4-2.7

  * Adding support of Python 3 and above is underway. This has proved to be 
    quite a challenge, as RPyC is tightly-coupled to the *object model* of the 
    language, so the porting will likely take a while.

* Jython 2.5 and later

* IronPython 2.7 and later


Development
===========

.. _mailing-list:

Mailing List
------------
Feel free to use our `mailing list <http://groups.google.com/group/rpyc>`_ to 
ask questions and join the discussion, but please **do not send bug reports
to the mailing list**. Please be sure to search the forum first, before asking
questions. For *bug reports*, see below.

Repository
----------
RPyC is developed on `github <http://github.com/tomerfiliba/rpyc>`_, where you
can always find the latest code or fork the project.

Bugs and Patches
----------------
We're using github's `issue tracker <http://github.com/tomerfiliba/rpyc/issues>`_
for bug reports, feature requests, and overall status. When stumbling upon what
seems to be a bug, be sure to open an issue rather than just sending a message
to the mailing list.

Patches are accepted **only** through github's `pull requests <http://help.github.com/pull-requests/>`_,
which provide a much more organized way to share patches: simply fork the 
project, commit your changes, and send a pull request. That way we can track,
discuss, and integrate patches much more easily and concisely. 

.. _dependencies:

Dependencies
------------
The core of RPyC has no external dependencies, so you can use it out of the 
box for "simlpe" use. However, RPyC integrates with some other projects to 
provide more features, and if you wish to use any of those, you must install
them:


* `TLSlite <http://trevp.net/tlslite/>`_ - Required for TLSlite support 
  (``VdbAuthenticator`` and ``tls_connect``). The project is no longer maintained,
  but you can download v0.3.8 `ported to newer versions of python 
  <http://sourceforge.net/projects/rpyc/files/tlslite/>`_ 

  * `PyCrypto <https://www.dlitz.net/software/pycrypto/>`_ - If installed, 
    will speed up TLSlite
    
  * `PyOpenSSL <https://launchpad.net/pyopenssl>`_ - If installed, will speed 
    up TLSlite 

* `ssl-wrapper <http://pypi.python.org/pypi/ssl/>`_ - Required for SSL support 
  on python prior to v2.6 (``ssl_connect``)

* SSH client - Required for RPyC-over-SSH (``ssh_connect``)

* `PyWin32 <http://sourceforge.net/projects/pywin32/files/pywin32/>`_ - Required 
  for ``PipeStream`` on Windows 
 
* `zlib for IronPython <https://bitbucket.org/jdhardy/ironpythonzlib>`_ - Required
  for IronPython prior to v2.7

.. _license:

License
=======
RPyC is released under the *MIT license*:

  .. literalinclude:: ../LICENSE



