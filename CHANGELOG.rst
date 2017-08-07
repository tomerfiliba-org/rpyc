3.4.4
-----
Date: 07.08.2017

* Fix refcount leakage when unboxing from cache (#196)
* Fix TypeError when dispatching exceptions on py2 (unicode)
* Respect ``rpyc_protocol_config`` for default Service getattr (#202)
* Support unix domain sockets (#100,#208)
* Use first accessible server in ``connect_by_service`` (#220)
* Fix deadlock problem with logging (#207,#212)


3.4.3
-----
Date: 26.07.2017

* Add missing endpoints config in ThreadPoolServer (#222)
* Fix jython support (#156,#171)
* Improve documentation (#158,#185,#189,#198 and more)

3.4.2
-----
Date: 14.06.2017

* Fix ``export_function`` on python 3.6

3.4.1
-----
Date: 09.06.2017

* Fix issue high-cpu polling (#191,#218)
* Fix filename argument in logging (#197)
* Improved log messages (#191,#204)
* Drop support for python 3.2 and py 2.5

3.4.0
-----
Date: 29.05.2017

Please excuse the briefity for this versions changelist.

* Add keepalive interface [#151]

* Various fixes: #136, #140, #143, #147, #149, #151, #159, #160, #166, #173, #176, #179, #174, #182, #183 and others.

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
* Fix (`issue #76 <https://github.com/tomerfiliba/rpyc/issues/76>`_) for real this time

* Fix issue with ``BgServingThread`` (`#89 <https://github.com/tomerfiliba/rpyc/issues/89>`_)

* Fix issue with ``ThreadPoolServer`` (`#91 <https://github.com/tomerfiliba/rpyc/issues/91>`_)

* Remove RPyC's ``excepthook`` in favor of chaining the exception's remote tracebacks in the
  exception class' ``__str__`` method. This solves numerous issues with logging and debugging.

* Add ``OneShotServer``

* Add `UNIX domain sockets <https://github.com/tomerfiliba/rpyc/pull/100>`_

3.2.2
-----
* Windows: make SSH tunnels windowless (`#68 <https://github.com/tomerfiliba/rpyc/issues/68>`_)

* Fixes a compatibility issue with IronPython on Mono
  (`#72 <https://github.com/tomerfiliba/rpyc/issues/72>`_)

* Fixes an issue with introspection when an ``AttributeError`` is expected
  (`#71 <https://github.com/tomerfiliba/rpyc/issues/71>`_)

* The server now logs all exceptions (`#73 <https://github.com/tomerfiliba/rpyc/issues/73>`_)

* Forking server: call ``siginterrupt(False)`` in forked child 
  (`#76 <https://github.com/tomerfiliba/rpyc/issues/76>`_)

* Shutting down the old wikidot site 

* Adding `Travis CI <http://travis-ci.org/#!/tomerfiliba/rpyc>`_ integration

3.2.1
-----
* Adding missing import (`#52 <https://github.com/tomerfiliba/rpyc/issues/52>`_)

* Fixing site documentation issue (`#54 <https://github.com/tomerfiliba/rpyc/issues/54>`_)

* Fixing Python 3 incompatibilities (`#58 <https://github.com/tomerfiliba/rpyc/issues/58>`_, 
  `#59 <https://github.com/tomerfiliba/rpyc/issues/59>`_, 
  `#60 <https://github.com/tomerfiliba/rpyc/issues/60>`_,
  `#61 <https://github.com/tomerfiliba/rpyc/issues/61>`_,
  `#66 <https://github.com/tomerfiliba/rpyc/issues/66>`_)

* Fixing ``slice`` issue (`#62 <https://github.com/tomerfiliba/rpyc/issues/62>`_)

* Added the ``endpoints`` parameter to the config dict of connection (only on the server side)

3.2.0
-----
* Added support for IPv6 (`#28 <https://github.com/tomerfiliba/rpyc/issues/28>`_)

* Added SSH tunneling support (``ssh_connect``)

* Added ``restricted`` object wrapping

* Several fixes to ``AsyncResult`` and weak references

* Added the ``ThreadPoolServer``

* Fixed some minor (harmless) races that caused tracebacks occasionally when 
  server-threads terminated

* Fixes issues `#8 <https://github.com/tomerfiliba/rpyc/issues/8>`_, 
  `#41 <https://github.com/tomerfiliba/rpyc/issues/41>`_, 
  `#42 <https://github.com/tomerfiliba/rpyc/issues/42>`_, 
  `#43 <https://github.com/tomerfiliba/rpyc/issues/43>`_,
  `#46 <https://github.com/tomerfiliba/rpyc/issues/46>`_, and
  `#49 <https://github.com/tomerfiliba/rpyc/issues/49>`_. 

* Converted all ``CRLF`` to ``LF`` (`#40 <https://github.com/tomerfiliba/rpyc/issues/40>`_)

* Dropped TLSlite integration (`#45 <https://github.com/tomerfiliba/rpyc/issues/45>`_).
  We've been dragging this corpse for too long.

* **New documentation** (both the website and docstrings) written in **Sphinx**

  * The site has moved to `sourceforge <http://rpyc.sourceforge.net>`_. Wikidot 
    had served us well over the past three years, but they began displaying way too 
    many ads and didn't support uploading files over ``rsync``, which made my life hard.

  * New docs are part of the git repository. Updating the site is as easy as
    ``make upload``

* **Python 3.0-3.2** support

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

