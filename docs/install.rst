.. _install:

Download and Install
====================

You can always download the latest releases of RPyC from the project's
`github page <https://github.com/tomerfiliba/rpyc/releases>`_ or
its `PyPI page <http://pypi.python.org/pypi/rpyc>`_. The easiest way to
install RPyC, however, is using::

    pip install rpyc

If you don't want to mess with virtualenvs or mess with system directories,
install as user::

    pip install rpyc --user

Be sure to read the :ref:`changelog <changelog>` before upgrading versions!
Also, always link your own applications against a fixed major version of
rpyc!

Platforms and Interpreters
--------------------------
RPyC is a pure-python library, and as such can run on any architecture and
platform that runs python (or one of its other implementations), both 32-
and 64-bit. This is also true for a client and its server, which may run on
different architectures. The latest release supports:

* **Python** (CPython) 2.7-3.7
* May work on py2.6
* May work with **Jython** and **IronPython**. However, these are not primary
  concerns for me. Breakage may occur at any time.

Cross-Interpreter Compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Note that you **cannot** connect from a **Python 2.x** interpreter to a **3.x**
one, or vice versa. Trying to do so will
results in all kinds of `strange exceptions
<https://github.com/tomerfiliba/rpyc/issues/54>`_, so beware. This is because Python 3 introduces major changes to
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

Big words aside -- you can connect from **Python 2.x to Python 2.y**, as
long as you only use types/modules/features supported by both; and you can
connect from **Python 3.x to Python 3.y**, under the same assumption.

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
There is an old `mailing list <http://groups.google.com/group/rpyc>`_ that may
contain useful information and that you should search before asking questions.
Nowadays however, do not count on getting any answers for new questions there.

Repository
----------
RPyC is developed on `github <http://github.com/tomerfiliba/rpyc>`_, where you
can always find the latest code or fork the project.

.. _bugs:

Bugs and Patches
----------------
We're using github's `issue tracker <http://github.com/tomerfiliba/rpyc/issues>`_
for bug reports, feature requests, and overall status.

Patches are accepted through github `pull requests <http://help.github.com/pull-requests/>`_.

.. _dependencies:

Dependencies
------------
The core of RPyC has no external dependencies, so you can use it out of the
box for "simple" use. However, RPyC integrates with some other projects to
provide more features, and if you wish to use any of those, you must install
them:

* `PyWin32 <http://sourceforge.net/projects/pywin32/files/pywin32/>`_ - Required
  for ``PipeStream`` on Windows

* `zlib for IronPython <https://bitbucket.org/jdhardy/ironpythonzlib>`_ - Required
  for IronPython prior to v2.7
