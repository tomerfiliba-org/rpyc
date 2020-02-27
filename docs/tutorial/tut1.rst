.. _tut1:

Part 1: Introduction to *Classic RPyC*
======================================

We'll kick-start the tutorial with what is known as *classic-style* RPyC, i.e., the
methodology of RPyC 2.60. Since RPyC 3 is a complete redesign of the library, there are some
minor changes, but if you were familiar with RPyC 2.60, you'll feel right at home. And even
if you were not -- we'll make sure you feel at home in a moment ;)

Running a Server
----------------
Let's start with the basics: running a server. In this tutorial we'll run both the server and
the client on the same machine (the ``localhost``). The classic server can be
started using::

    $ python bin/rpyc_classic.py
    INFO:SLAVE/18812:server started on [127.0.0.1]:18812

This shows the parameters this server is running with:

- ``SLAVE`` indicates the ``SlaveService`` (you'll learn more about
  :ref:`services <services>` later on), and

- ``[127.0.0.1]:18812`` is the address on which the server binds, in this case
  the server will only accept connections from localhost. If you run a server
  with ``--host 0.0.0.0``, you are free for arbitrary code execution from
  anywhere.

Running a Client
----------------
The next step is running a client which connects to the server. The code needed to create a
connection to the server is quite simple, you'd agree ::

    import rpyc
    conn = rpyc.classic.connect("localhost")

If your server is not running on the default port (``TCP 18812``), you'll have
to pass the ``port=`` parameter to :func:`.classic.connect`.

The ``modules`` Namespace
-------------------------
The ``modules`` property of connection objects exposes the server's
module-space, i.e., it lets you access remote modules. Here's how::

    rsys = conn.modules.sys     # remote module on the server!

This *dot notation* only works for top level modules. Whenever you would
require a nested import for modules contained within a package, you have to
use the *bracket notation* to import the remote module, e.g.::

    minidom = conn.modules["xml.dom.minidom"]

With this alone you are already set to do almost anything. For example, here
is how you see the server's command line::

    >>> rsys.argv
    ['bin/rpyc_classic.py']

…add module search pathes for the server's import mechanism::

    >>> rsys.path.append('/tmp/totally-secure-package-location)

…change the current working directory of the server process::

    >>> conn.modules.os.chdir('..')

…or even print something on the server's stdout:

    >>> print("Hello World!", file=conn.modules.sys.stdout)


The ``builtins`` Namespace
---------------------------

The ``builtins`` property of classic connection exposes all builtin functions
available in the server's python environment. You could use it for example to
access a file on the server:

    >>> f = conn.builtins.open('/home/oblivious/.ssh/id_rsa')
    >>> f.read()
    '-----BEGIN RSA PRIVATE KEY-----\nMIIJKQIBAAKCAgEA0...XuVmz/ywq+5m\n-----END RSA PRIVATE KEY-----\n'

Ooopsies, I just leaked my private key…;)

The ``eval`` and ``execute`` Methods
------------------------------------
If you are not satisfied already, here is more: Classic connections also have
properties ``eval`` and ``execute`` that allow you to directly evaluate
arbitrary expressions or even execute arbitrary statements on the server.
For example::

    >>> conn.execute('import math')
    >>> conn.eval('2*math.pi')
    6.283185307179586

But wait, this requires that rpyc classic connections have some notion of
global variables, how can you see them? They are accessible via the
``namespace`` property that will be initialized as empty dictionary for every
new connection. So, after our import, we now have::

    >>> conn.namespace
    {'__builtins__': <...>, 'math': <...>}

The aware reader will have noticed that neither of these shenanigans are
strictly needed, as the same functionality could be achieved by using the
``conn.builtins.compile()`` function, which is also accessible via
``conn.modules.builtins.compile()``, and manually feeding it with a remotely
created dict.

That's true, but we sometimes like a bit of sugar;)


The ``teleport`` method
-----------------------
There is another interesting method that allows you to transmit functions to
the other sides and execute them over there::

   >>> def square(x):
   ...    return x**2
   >>> fn = conn.teleport(square)
   >>> fn(2)

This calculates the square of two as expected, but the computation takes place
on the remote!

Furthermore, teleported functions are automatically defined in the remote
namespace::

   >>> conn.eval('square(3)')
   9

   >>> conn.namespace['square'] is fn
   True

And the teleported code can also access the namespace::

   >>> conn.execute('import sys')
   >>> version = conn.teleport(lambda: print(sys.version_info))
   >>> version()

prints the version on the remote terminal.

Note that currently it is not possible to teleport arbitrary functions, in
particular there can be issues with closures to non-trivial objects. In case
of problems it may be worth taking a look at external libraries such as dill_.

.. _dill: https://pypi.org/project/dill/

Continue to :ref:`tut2`...
