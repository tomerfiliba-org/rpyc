.. _install:

Download and Install
====================

You can always download the latest releases of RPyC from the project's
`sourceforge page <http://sourceforge.net/projects/rpyc/files/main>`_ or
its `PyPI page <http://pypi.python.org/pypi/rpyc>`_. RPyC is distributed as a
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

* **Python** (CPython) 2.4-2.7 as well as 3.0-3.2
* **Jython** 2.5 and later
* **IronPython** 2.7 and later

Cross-Interpreter Compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Note that you **cannot** connect from a **Python 2.x** interpreter to a **3.x**
one, or vice versa. This is because Python 3 introduces major changes to
the object model used by Python 2.x: some types were removed, added or
unified into others. Byte- and Unicode- strings gave me a nightmare (and they
still account for many bugs in the core interpreter). On top of that,
many built-in modules and functions were renamed or removed, and many new
language features were added. These changes render the two major versions
of Python incompatible with one another, and sadly, this cannot be bridged
automatically by RPyC at the serialization layer.

It's not that I didn't try -- it's just too hard a feat. It's bascially like
writing a 100% working `2to3 <http://docs.python.org/library/2to3.html>`_ tool,
alongside with a matching ``3to2`` one; and that, I reckon, is comparable to
the *halting problem* (of course I might be wrong here, but it still doesn't
make it feasible).

Big words aside -- you can connect a Python 2.x interpreter to a Python 2.y
one, as long as you only use types/modules/features supported by both; and
you can connect a Python 3.x interpreter to a Python 3.y one, under the same
assumption, but you cannot connect a Python 2.x interpreter to a 3.y one.
Trying to do so will results in all kinds of `strange exceptions
<https://github.com/tomerfiliba/rpyc/issues/54>`_, so beware.

.. note::
   As a side note, do not try to mix different versions of RPyC (e.g., connecting
   a client machine running RPyC 3.1.0 to a server running RPyC 3.2.0). The
   wire-protocol has seen little changes since the release of RPyC 3.0, but the
   library itself has changed drastically. This might work, but don't count on it.

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

.. _bugs:

Bugs and Patches
----------------
We're using github's `issue tracker <http://github.com/tomerfiliba/rpyc/issues>`_
for bug reports, feature requests, and overall status. When stumbling upon what
seems to be a bug, you may consult with the mailing list, but be sure to open
an issue as well.

Patches are accepted **only** through github's `pull requests <http://help.github.com/pull-requests/>`_
mechanism, which provides a much more organized way to share patches: simply fork
the project, commit your changes, and send a pull request. That way we can track,
discuss, and integrate patches much more easily and concisely.

.. _dependencies:

Dependencies
------------
The core of RPyC has no external dependencies, so you can use it out of the
box for "simple" use. However, RPyC integrates with some other projects to
provide more features, and if you wish to use any of those, you must install
them:

* `PyWin32 <http://sourceforge.net/projects/pywin32/files/pywin32/>`_ - Required
  for ``PipeStream`` on Windows

* SSH client - Required for :ref:`RPyC-over-SSH <ssh-tunneling>` (``ssh_connect``)

* Compatibiliy dependencies:

  * `ssl-wrapper <http://pypi.python.org/pypi/ssl/>`_ - Required for SSL support
    on python prior to v2.6 (``ssl_connect``)

  * `TLSlite <http://trevp.net/tlslite/>`_ - Required for TLSlite support
    (``VdbAuthenticator`` and ``tls_connect``). The project is no longer maintained,
    but you can download v0.3.8 `ported to newer versions of python
    <http://sourceforge.net/projects/rpyc/files/tlslite/>`_.

    .. note::
       **TLSLite has been deprecated** as of v3.2.0, and can only be used with v3.1.0 and below.

  * `zlib for IronPython <https://bitbucket.org/jdhardy/ironpythonzlib>`_ - Required
    for IronPython prior to v2.7


