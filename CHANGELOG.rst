3.1.0
------

What's New:
^^^^^^^^^^^
* Supports CPython 2.4-2.7, IronPython, and Jython

* `tlslite <http://sourceforge.net/projects/rpyc/files/tlslite>`_ has been ported to
  python 2.5-2.7 (the original library targeted 2.3 and 2.4)

* Initial python 3 support -- not finished!

* Moves to a more conventional directory structure

* Moves to more standard facilities (logging, nosetests)

* Solves a major performance issue with the ``BgServingThread`` (`#32 <https://github.com/tomerfiliba/rpyc/issues/32>`_),
  by removing the contention between the two threads that share the connection

* Fixes lots of issues concerning the ForkingServer (`#3 <http://github.com/tomerfiliba/rpyc/issues/3>`_,
  `#7 <http://github.com/tomerfiliba/rpyc/issues/7>`_, and `#15 <http://github.com/tomerfiliba/rpyc/issues/15>`_)

* Many small bug fixes (`#16 <http://github.com/tomerfiliba/rpyc/issues/16>`_,
  `#13 <http://github.com/tomerfiliba/rpyc/issues/13>`_,
  `#4 <http://github.com/tomerfiliba/rpyc/issues/4>`_, etc.)

* Integrates with the built-in ``ssl`` module for SSL support

  * ``rpyc_classic.py`` now takes several ``--ssl-xxx`` switches (see ``--help``
    for more info)

* Fixes typos, running pylint, etc.

Breakage from 3.0.7:
^^^^^^^^^^^^^^^^^^^^
* Removing egg builds (we're pure python, and eggs just messed up the build)

* Package layout changed drastically, and some files were renamed

  * The ``servers/`` directory was renamed ``scripts/``

  * ``classic_server.py`` was renamed ``rpyc_classic.py``

  * They scripts now install to your python scripts directory (no longer part
    of the package), e.g. ``C:\python27\Scripts``

* ``rpyc_classic.py`` now takes ``--register`` in order to register,
  instead of ``--dont-register``, which was a silly choice.

* ``classic.tls_connect``, ``factory.tls_connect`` were renamed ``tlslite_connect``,
  to distinguish it from the new ``ssl_connect``.


3.0.7
-----
* Moving to **git** as source control

* Build script: more egg formats; register in `pypi <http://pypi.python.org/pypi/RPyC/>`_ ;
  remove svn; auto-generate ``license.py`` as well

* Cosmetic touches to ``Connection``: separate ``serve`` into ``_recv`` and ``dispatch``

* Shutdown socket before closing (``SHUT_RDWR``) to prevent ``TIME_WAIT`` and other
  problems with various *nixes

* ``PipeStream``: use low-level file APIs (``os.read``, ``os.write``) to prevent
  stdio-level buffering that messed up ``select``

* ``classic_server.py``: open logfile for writing (was opened for reading)

* ``registry_server.py``: type of ``timeout`` is now ``int`` (was ``str``)

* ``utils/server.py``: better handling of sockets; fix python 2.4 syntax issue

* ``ForkingServer``: re-register ``SIGCHLD`` handler after handling that signal,
  to support non-BSD-compliant platforms where after the invocation of the signal
  handler, the handler is reset


3.0.6
-----
* Handle metaclasses better in ``inspect_methods``

* ``vinegar.py``: handle old-style-class exceptions better; python 2.4 issues

* ``VdbAuthenticator``: when loading files, open for read only; API changes
  (``from_dict`` instead of ``from_users``), ``from_file`` accepts open-mode

* ``ForkingServer``: better handling of SIGCHLD


3.0.5
-----
* ``setup.py`` now also creates egg files

* Slightly improved ``servers/vdbconf.py``

* Fixes to ``utis/server.py``:

  * The authenticator is now invoked by ``_accept_client``, which means it is invoked
    on the client's context (thread or child process). This solves a problem with
    the forking server having a TLS authenticator.

  * Changed the forking server to handle ``SIGCHLD`` instead of using double-fork.


3.0.4
-----
* Fix: ``inspect_methods`` used ``dir`` and ``getattr`` to inspect the given object;
  this caused a problem with premature activation of properties (as they are
  activated by ``getattr``). Now it inspects the object's type instead, following
  the MRO by itself, to avoid possible side effects.


3.0.3
-----
* Changed versioning scheme: now 3.0.3 instead of 3.03, and the version tuple is (3, 0, 3)

* Added ``servers/vdbconf.py`` - a utility to manage verifier databases (used by ``tlslite``)

* Added the ``--vdb`` switch to ``classic_server.py``, which invokes a secure server
  (TLS) with the given VDB file.


3.02
----
* Authenticators: authenticated servers now store the credentials of the connection
  in conn._config.credentials

* ``Registry``: added UDP and TCP registry servers and clients (``from rpyc.utils.registry import ...``)

* Minor bug fixes

* More tests

* The test-suite now runs under python 2.4 too


3.01
----
* Fixes some minor issues/bugs

* The registry server can now be instantiated (no longer a singleton) and customized,
  and RPyC server can be customized to use the different registry.


3.00
----

Known Issues
^^^^^^^^^^^^
* **comparison** - comparing remote and local objects will usually not work, but
  there's nothing to do about it.

* **64bit platforms**: since channels use 32bit length field, you can't pass
  data/strings over 4gb. this is not a real limitation (unless you have a super-fast
  local network and tons of RAM), but as 64bit python becomes the defacto standard,
  I will upgrade channels to 64bit length field.

* **threads** - in face of no better solution, and after consulting many people,
  I resorted to setting a timeout on the underlying recv(). This is not an elegant
  way, but all other solution required rewriting all sorts of threading primitives
  and were not necessarily deadlock/race-free. as the zen says, "practicality beats purity".

* Windows - pipes supported, but Win32 pipes work like shit

3.00 RC2
--------
Known Issues
^^^^^^^^^^^^
* Windows - pipe server doesn't work

