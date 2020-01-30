4.1.4
-----
Date: 1.30.2020

- Merged 3.7 and 3.8 teleportatio compat enhancement `#371`_
- Fixed connection hanging due to namepack cursor  `#369`_
- Fixed test dependencies and is_py_* for 3.9

.. _#371: https://github.com/tomerfiliba/rpyc/issues/371
.. _#369: https://github.com/tomerfiliba/rpyc/issues/369

4.1.3
-----
Date: 1.25.2020

- Performance improvements: `#366`_ and `#351`_
- Merged fix for propagate_KeyboardInterrupt_locally `#364`_
- Fixed handling of exceptions for request callbacks `#365`_
- Partially fixed return value for netref.__class__ `#355`_

.. _#366: https://github.com/tomerfiliba/rpyc/issues/366
.. _#351: https://github.com/tomerfiliba/rpyc/pull/351
.. _#364: https://github.com/tomerfiliba/rpyc/pull/364
.. _#365: https://github.com/tomerfiliba/rpyc/issues/365
.. _#355: https://github.com/tomerfiliba/rpyc/issues/355


4.1.2
-----
Date: 10.03.2019

- Fixed `CVE-2019-16328`_ which was caused by a missing protocol security check
- Fixed RPyC over RPyC for mutable parameters and extended unit testing for `#346`_

.. _CVE-2019-16328: https://rpyc.readthedocs.io/en/latest/docs/security.html
.. _#346: https://github.com/tomerfiliba/rpyc/issues/346


4.1.1
-----
Date: 07.27.2019

- Fixed netref.class_factory id_pack usage per #339 and added test cases
- Name pack casted in _unbox to fix IronPython bug. Fixed #337
- Increased chunk size to improve multi-client response time and throughput of large data #329
- Added warning to _remote_tb when the major version of local and remote mismatch (#332)
- OneShotServer termination was fixed by WilliamBruneau (#343)
- Known issue with 3.8 for CodeType parameters (may drop Python2 support first)


4.1.0
-----
Date: 05.25.2019

- Added connection back-off and attempts for congested workloads
- Fixed minor resource leak for ForkingServer (#304)
- Cross-connection instance check for cached netref classes (#316)
- Hashing fixed (#324)
- New ID Pack convention breaks compatibility between a client/server >= 4.10 with a client/server < 4.10


4.0.2
-----
Date: 04.08.2018

- fix default hostname for ipv6 in rpyc_classic.py (#277)
- fix ThreadPoolServer not working (#283)


4.0.1
-----
Date: 12.06.2018

- fix ValueError during install due to absolute PATH in SOURCES.txt (`#276`_)

.. _#276: https://github.com/tomerfiliba/rpyc/issues/276


4.0.0
-----
Date: 11.06.2018

This release brings a few minor backward incompatibilities, so be sure to read
on before upgrading. However, fear not: the ones that are most likely relevant
to you have a relatively simple migration path.

Backward Incompatibilities
^^^^^^^^^^^^^^^^^^^^^^^^^^

* ``classic.teleport_function`` now executes the function in the connection's
  namespace by default. To get the old behaviour, use
  ``teleport_function(conn, func, conn.modules[func.__module__].__dict__)``
  instead.

* Changed signature of ``Service.on_connect`` and ``on_disconnect``, adding
  the connection as argument.

* Changed signature of ``Service.__init__``, removing the connection argument

* no longer store connection as ``self._conn``. (allows services that serve
  multiple clients using the same service object, see `#198`_).

* ``SlaveService`` is now split into two asymetric classes: ``SlaveService``
  and ``MasterService``. The slave exposes functionality to the master but can
  not anymore access remote objects on the master (`#232`_, `#248`_).
  If you were previously using ``SlaveService``, you may experience problems
  when feeding the slave with netrefs to objects on the master. In this case, do
  any of the following:

  * use ``ClassicService`` (acts exactly like the old ``SlaveService``)
  * use ``SlaveService`` with a ``config`` that allows attribute access etc
  * use ``rpyc.utils.deliver`` to feed copies rather than netrefs to
    the slave

* ``RegistryServer.on_service_removed`` is once again called whenever a service
  instance is removed, making it symmetric to ``on_service_added`` (`#238`_)
  This reverts PR `#173`_ on issue `#172`_.

* Removed module ``rpyc.experimental.splitbrain``. It's too confusing and
  undocumented for me and I won't be developing it, so better remove it
  altogether. (It's still available in the ``splitbrain`` branch)

* Removed module ``rpyc.experimental.retunnel``. Seemingly unused anywhere, no
  documentation, no clue what this is about.

* ``bin/rpyc_classic.py`` will bind to ``127.0.0.1`` instead of ``0.0.0.0`` by
  default

* ``SlaveService`` no longer serves exposed attributes (i.e., it now uses
  ``allow_exposed_attrs=False``)

* Exposed attributes no longer hide plain attributes if one otherwise has the
  required permissions to access the plain attribute. (`#165`_)

.. _#165: https://github.com/tomerfiliba/rpyc/issues/165
.. _#172: https://github.com/tomerfiliba/rpyc/issues/172
.. _#173: https://github.com/tomerfiliba/rpyc/issues/173
.. _#198: https://github.com/tomerfiliba/rpyc/issues/198
.. _#232: https://github.com/tomerfiliba/rpyc/issues/232
.. _#238: https://github.com/tomerfiliba/rpyc/issues/238
.. _#248: https://github.com/tomerfiliba/rpyc/issues/248

What else is new
^^^^^^^^^^^^^^^^

* teleported functions will now be defined by default in the globals dict

* Can now explicitly specify globals for teleported functions

* Can now use streams as context manager

* keep a hard reference to connection in netrefs, may fix some ``EOFError``
  issues, in particular on Jython related (`#237`_)

* handle synchronous and asynchronous requests uniformly

* fix deadlock with connections talking to each other multithreadedly (`#270`_)

* handle timeouts cumulatively

* fix possible performance bug in ``Win32PipeStream.poll`` (oversleeping)

* use readthedocs theme for documentation (`#269`_)

* actually time out sync requests (`#264`_)

* clarify documentation concerning exceptions in ``Connection.ping`` (`#265`_)

* fix ``__hash__`` for netrefs (`#267`_, `#268`_)

* rename ``async`` module to ``async_`` for py37 compatibility (`#253`_)

* fix ``deliver()`` from IronPython to CPython2 (`#251`_)

* fix brine string handling in py2 IronPython (`#251`_)

* add gevent_ Server. For now, this requires using ``gevent.monkey.patch_all()``
  before importing for rpyc. Client connections can already be made without
  further changes to rpyc, just using gevent's monkey patching. (`#146`_)

* add function ``rpyc.lib.spawn`` to spawn daemon threads

* fix several bugs in ``bin/rpycd.py`` that crashed this script on startup
  (`#231`_)

* fix problem with MongoDB, or more generally any remote objects that have a
  *catch-all* ``__getattr__`` (`#165`_)

* fix bug when copying remote numpy arrays (`#236`_)

* added ``rpyc.utils.helpers.classpartial`` to bind arguments to services (`#244`_)

* can now pass services optionally as instance or class (could only pass as
  class, `#244`_)

* The service is now charged with setting up the connection, doing so in
  ``Service._connect``. This allows using custom protocols by e.g. subclassing
  ``Connection``.  More discussions and related features in `#239`_-`#247`_.

* service can now easily override protocol handlers, by updating
  ``conn._HANDLERS`` in ``_connect`` or ``on_connect``. For example:
  ``conn._HANDLERS[HANDLE_GETATTR] = self._handle_getattr``.

* most protocol handlers (``Connection._handle_XXX``) now directly get the
  object rather than its ID as first argument. This makes overriding
  individual handlers feel much more high-level. And by the way it turns out
  that this fixes two long-standing issues (`#137`_, `#153`_)

* fix bug with proxying context managers (`#228`_)

* expose server classes from ``rpyc`` top level module

* fix logger issue on jython

.. _#137: https://github.com/tomerfiliba/rpyc/issues/137
.. _#146: https://github.com/tomerfiliba/rpyc/issues/146
.. _#153: https://github.com/tomerfiliba/rpyc/issues/153
.. _#165: https://github.com/tomerfiliba/rpyc/issues/165
.. _#228: https://github.com/tomerfiliba/rpyc/issues/228
.. _#231: https://github.com/tomerfiliba/rpyc/issues/231
.. _#236: https://github.com/tomerfiliba/rpyc/issues/236
.. _#237: https://github.com/tomerfiliba/rpyc/issues/237
.. _#239: https://github.com/tomerfiliba/rpyc/issues/239
.. _#244: https://github.com/tomerfiliba/rpyc/issues/244
.. _#247: https://github.com/tomerfiliba/rpyc/issues/247
.. _#251: https://github.com/tomerfiliba/rpyc/issues/251
.. _#253: https://github.com/tomerfiliba/rpyc/issues/253
.. _#264: https://github.com/tomerfiliba/rpyc/issues/264
.. _#265: https://github.com/tomerfiliba/rpyc/issues/265
.. _#267: https://github.com/tomerfiliba/rpyc/issues/267
.. _#268: https://github.com/tomerfiliba/rpyc/issues/268
.. _#269: https://github.com/tomerfiliba/rpyc/issues/269
.. _#270: https://github.com/tomerfiliba/rpyc/issues/270

.. _gevent: http://www.gevent.org/

3.4.4
-----
Date: 07.08.2017

* Fix refcount leakage when unboxing from cache (`#196`_)
* Fix TypeError when dispatching exceptions on py2 (unicode)
* Respect ``rpyc_protocol_config`` for default Service getattr (`#202`_)
* Support unix domain sockets (`#100`_, `#208`_)
* Use first accessible server in ``connect_by_service`` (`#220`_)
* Fix deadlock problem with logging (`#207`_, `#212`_)
* Fix timeout problem for long commands (`#169`_)

.. _#100: https://github.com/tomerfiliba/rpyc/issues/100
.. _#169: https://github.com/tomerfiliba/rpyc/issues/169
.. _#196: https://github.com/tomerfiliba/rpyc/issues/196
.. _#202: https://github.com/tomerfiliba/rpyc/issues/202
.. _#207: https://github.com/tomerfiliba/rpyc/issues/207
.. _#208: https://github.com/tomerfiliba/rpyc/issues/208
.. _#212: https://github.com/tomerfiliba/rpyc/issues/212
.. _#220: https://github.com/tomerfiliba/rpyc/issues/220

3.4.3
-----
Date: 26.07.2017

* Add missing endpoints config in ThreadPoolServer (`#222`_)
* Fix jython support (`#156`_, `#171`_)
* Improve documentation (`#158`_, `#185`_, `#189`_, `#198`_ and more)

.. _#156: https://github.com/tomerfiliba/rpyc/issues/156
.. _#158: https://github.com/tomerfiliba/rpyc/issues/158
.. _#171: https://github.com/tomerfiliba/rpyc/issues/171
.. _#185: https://github.com/tomerfiliba/rpyc/issues/185
.. _#189: https://github.com/tomerfiliba/rpyc/issues/189
.. _#198: https://github.com/tomerfiliba/rpyc/issues/198
.. _#222: https://github.com/tomerfiliba/rpyc/issues/222

3.4.2
-----
Date: 14.06.2017

* Fix ``export_function`` on python 3.6

3.4.1
-----
Date: 09.06.2017

* Fix issue high-cpu polling (`#191`_, `#218`_)
* Fix filename argument in logging (`#197`_)
* Improved log messages (`#191`_, `#204`_)
* Drop support for python 3.2 and py 2.5

.. _#191: https://github.com/tomerfiliba/rpyc/issues/191
.. _#197: https://github.com/tomerfiliba/rpyc/issues/197
.. _#204: https://github.com/tomerfiliba/rpyc/issues/204
.. _#218: https://github.com/tomerfiliba/rpyc/issues/218

3.4.0
-----
Date: 29.05.2017

Please excuse the briefity for this versions changelist.

* Add keepalive interface [`#151`_]

* Various fixes: `#136`_, `#140`_, `#143`_, `#147`_, `#149`_, `#151`_, `#159`_, `#160`_, `#166`_, `#173`_, `#176`_, `#179`_, `#174`_, `#182`_, `#183`_ and others.

.. _#136: https://github.com/tomerfiliba/rpyc/issues/136
.. _#140: https://github.com/tomerfiliba/rpyc/issues/140
.. _#143: https://github.com/tomerfiliba/rpyc/issues/143
.. _#147: https://github.com/tomerfiliba/rpyc/issues/147
.. _#149: https://github.com/tomerfiliba/rpyc/issues/149
.. _#151: https://github.com/tomerfiliba/rpyc/issues/151
.. _#159: https://github.com/tomerfiliba/rpyc/issues/159
.. _#160: https://github.com/tomerfiliba/rpyc/issues/160
.. _#166: https://github.com/tomerfiliba/rpyc/issues/166
.. _#173: https://github.com/tomerfiliba/rpyc/issues/173
.. _#174: https://github.com/tomerfiliba/rpyc/issues/174
.. _#176: https://github.com/tomerfiliba/rpyc/issues/176
.. _#179: https://github.com/tomerfiliba/rpyc/issues/179
.. _#182: https://github.com/tomerfiliba/rpyc/issues/182
.. _#183: https://github.com/tomerfiliba/rpyc/issues/183

3.3.0
-----
* RPyC integrates with `plumbum <http://pypi.python.org/pypi/plumbum>`_; plumbum is required
  for some features, like ``rpyc_classic.py`` and *zero deploy*, but the core of the library
  doesn't require it. It is, of course, advised to have it installed.

* ``SshContext``, ``SshTunnel`` classes killed in favor of plumbum's SSH tunneling. The interface
  doesn't change much, except that ``ssh_connect`` now accept a ``plumbum.SshMachine`` instance
  instead of ``SshContext``.

* Zero deploy: deploy RPyC to a remote machine over an SSH connection and form an SSH tunnel
  connected to it, in just one line of code. All you need is SSH access and a Python interpreter
  installed on the remote machine.

* Dropping Python 2.4 support. RPyC now requires Python 2.5 - 3.3.

* rpycd - a well-behaved daemon for ``rpyc_classic.py``, based on
  `python-daemon <http://pypi.python.org/pypi/python-daemon/>`_

* The ``OneShotServer`` is now exposed by ``rpyc_classic -m oneshot``

* ``scripts`` directory renamed ``bin``

* Introducing ``Splitbrain Python`` - running code on remote machines transparently. Although tested,
  it is still considered experimental.

* Removing the ``BgServerThread`` and all polling/timeout hacks in favor of a "global background
  reactor thread" that handles all incoming transport from all connections. This should solve
  all threading issues once and for all.

* Added ``MockClassicConnection`` - a mock RPyC "connection" that allows you to write code that runs
  either locally or remotely without modification

* Added ``teleport_function``


3.2.3
-----
* Fix (issue `#76`_) for real this time

* Fix issue with ``BgServingThread`` (`#89`_)

* Fix issue with ``ThreadPoolServer`` (`#91`_)

* Remove RPyC's ``excepthook`` in favor of chaining the exception's remote tracebacks in the
  exception class' ``__str__`` method. This solves numerous issues with logging and debugging.

* Add ``OneShotServer``

* Add UNIX domain sockets (`#100`_)

.. _#76: https://github.com/tomerfiliba/rpyc/issues/76
.. _#89: https://github.com/tomerfiliba/rpyc/issues/89
.. _#91: https://github.com/tomerfiliba/rpyc/issues/91
.. _#100: https://github.com/tomerfiliba/rpyc/issues/100

3.2.2
-----
* Windows: make SSH tunnels windowless (`#68`_)

* Fixes a compatibility issue with IronPython on Mono (`#72`_)

* Fixes an issue with introspection when an ``AttributeError`` is expected (`#71`_)

* The server now logs all exceptions (`#73`_)

* Forking server: call ``siginterrupt(False)`` in forked child (`#76`_)

* Shutting down the old wikidot site

* Adding `Travis CI <http://travis-ci.org/#!/tomerfiliba/rpyc>`_ integration

.. _#68: https://github.com/tomerfiliba/rpyc/issues/68
.. _#71: https://github.com/tomerfiliba/rpyc/issues/71
.. _#72: https://github.com/tomerfiliba/rpyc/issues/72
.. _#73: https://github.com/tomerfiliba/rpyc/issues/73
.. _#76: https://github.com/tomerfiliba/rpyc/issues/76

3.2.1
-----
* Adding missing import (`#52`_)

* Fixing site documentation issue (`#54`_)

* Fixing Python 3 incompatibilities (`#58`_, `#59`_, `#60`_, `#61`_, `#66`_)

* Fixing ``slice`` issue (`#62`_)

* Added the ``endpoints`` parameter to the config dict of connection (only on the server side)

.. _#52: https://github.com/tomerfiliba/rpyc/issues/52
.. _#54: https://github.com/tomerfiliba/rpyc/issues/54
.. _#58: https://github.com/tomerfiliba/rpyc/issues/58
.. _#59: https://github.com/tomerfiliba/rpyc/issues/59
.. _#60: https://github.com/tomerfiliba/rpyc/issues/60
.. _#61: https://github.com/tomerfiliba/rpyc/issues/61
.. _#62: https://github.com/tomerfiliba/rpyc/issues/62
.. _#66: https://github.com/tomerfiliba/rpyc/issues/66

3.2.0
-----
* Added support for IPv6 (`#28`_)

* Added SSH tunneling support (``ssh_connect``)

* Added ``restricted`` object wrapping

* Several fixes to ``AsyncResult`` and weak references

* Added the ``ThreadPoolServer``

* Fixed some minor (harmless) races that caused tracebacks occasionally when
  server-threads terminated

* Fixes issues `#8`_, `#41`_, `#42`_, `#43`_, `#46`_, and `#49`_.

* Converted all ``CRLF`` to ``LF`` (`#40`_)

* Dropped TLSlite integration (`#45`_).
  We've been dragging this corpse for too long.

* **New documentation** (both the website and docstrings) written in **Sphinx**

  * The site has moved to `sourceforge <http://rpyc.sourceforge.net>`_. Wikidot
    had served us well over the past three years, but they began displaying way too
    many ads and didn't support uploading files over ``rsync``, which made my life hard.

  * New docs are part of the git repository. Updating the site is as easy as
    ``make upload``

* **Python 3.0-3.2** support

.. _#8: https://github.com/tomerfiliba/rpyc/issues/8
.. _#28: https://github.com/tomerfiliba/rpyc/issues/28
.. _#40: https://github.com/tomerfiliba/rpyc/issues/40
.. _#41: https://github.com/tomerfiliba/rpyc/issues/41
.. _#42: https://github.com/tomerfiliba/rpyc/issues/42
.. _#43: https://github.com/tomerfiliba/rpyc/issues/43
.. _#45: https://github.com/tomerfiliba/rpyc/issues/45
.. _#46: https://github.com/tomerfiliba/rpyc/issues/46
.. _#49: https://github.com/tomerfiliba/rpyc/issues/49

3.1.0
------

What's New
^^^^^^^^^^
* Supports CPython 2.4-2.7, IronPython, and Jython

* `tlslite <http://sourceforge.net/projects/rpyc/files/tlslite>`_ has been ported to
  python 2.5-2.7 (the original library targeted 2.3 and 2.4)

* Initial python 3 support -- not finished!

* Moves to a more conventional directory structure

* Moves to more standard facilities (``logging``, ``nosetests``)

* Solves a major performance issue with the ``BgServingThread`` (`#32`_),
  by removing the contention between the two threads that share the connection

* Fixes lots of issues concerning the ForkingServer (`#3`_, `#7`_, and `#15`_)

* Many small bug fixes (`#16`_, `#13`_, `#4`_, etc.)

* Integrates with the built-in ``ssl`` module for SSL support

  * ``rpyc_classic.py`` now takes several ``--ssl-xxx`` switches (see ``--help``
    for more info)

* Fixes typos, running pylint, etc.

.. _#3: https://github.com/tomerfiliba/rpyc/issues/3
.. _#4: https://github.com/tomerfiliba/rpyc/issues/4
.. _#7: https://github.com/tomerfiliba/rpyc/issues/7
.. _#13: https://github.com/tomerfiliba/rpyc/issues/13
.. _#15: https://github.com/tomerfiliba/rpyc/issues/15
.. _#16: https://github.com/tomerfiliba/rpyc/issues/16
.. _#32: https://github.com/tomerfiliba/rpyc/issues/32

Breakage from 3.0.7
^^^^^^^^^^^^^^^^^^^
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
  problems with various Unixes

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

