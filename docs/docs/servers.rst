.. _servers:

RPyC Servers
============

Since RPyC is a symmetric protocol (where both client and server can process requests),
an :ref:`RPyC server <api-server>` is a largely just a main-loop that accepts incoming
connections and calls :func:`serve_all <rpyc.core.protocol.Connection.serve_all>`. RPyC comes
with three built-in servers:

* Forking - forks a child-process to handle each incoming connection (POSIX only)
* Threaded - spawns a thread to handle each incoming connection (POSIX and Windows)
* Thread Pool - assigns a worker-thread for each incoming connection from the thread pool; if the
  thread pool is exhausted, the connection is dropped.

If you wish to implement new servers (say, reactor-based, etc.), you can derive from
:class:`rpyc.utils.server.Server` and implement ``_accept_method()`` to your own liking.

.. note::
   RPyC uses the notion of *authenticators* to authenticate incoming connections. An authenticator
   object can be passed to the server instance upon construction, and it is used to validate
   incoming connections. See :ref:`api-authenticators` for more info.


.. _classic-server:

Classic Server
--------------
RPyC comes "bundled" with a :ref:`classic`-mode server -- :file:`rpyc_classic.py`. This executable
script takes several command-line switches and starts an RPyC server exposing the
``ClassicService``. It is installed to your python's ``scripts/`` directory, and should be
executable from the command line. Example usage::

    $ ./rpyc_classic.py -m threaded -p 12333
    INFO:SLAVE/12333:server started on [0.0.0.0]:12333
    INFO:SLAVE/12333:accepted 127.0.0.1:34044
    INFO:SLAVE/12333:welcome [127.0.0.1]:34044
    INFO:SLAVE/12333:goodbye [127.0.0.1]:34044
    ^C
    WARNING:SLAVE/12333:keyboard interrupt!
    INFO:SLAVE/12333:server has terminated
    INFO:SLAVE/12333:listener closed


The classic server takes the following command-line switches (try running it with ``-h`` for
more info):

General switches
^^^^^^^^^^^^^^^^
* ``-m``, ``--mode=MODE`` - the serving mode (``threaded``, ``forking``, or ``stdio``). The default is
  ``threaded``; ``stdio`` is useful for integration with inetd.

* ``-p``, ``--port=PORT`` - the TCP port (only useful for ``threaded`` or ``forking`` modes). The
  default is ``18812``; for SSL the default is ``18821``.

* ``--host=HOSTNAME`` - the host to bind to. The default is ``0.0.0.0``.

* ``--ipv6`` - if given, binds an IPv6 socket. Otherwise, binds an IPv4 socket (the default).

* ``--logfile=FILENAME`` - the log file to use. The default is ``stderr``

* ``-q``, ``--quiet`` - if given, sets quiet mode (no logging).

Registry switches
^^^^^^^^^^^^^^^^^
* ``--register`` - if given, the server will attempt to register with a registry server. By default,
  the server will **not** attempt to register.

The following switches are only relevant in conjunction with ``--register``:

* ``--registry-type=REGTYPE`` - The registry type (``UDP`` or ``TCP``). The default is ``UDP``,
  where the server sends timely UDP broadcasts, aimed at the registry server.

* ``--registry-port=REGPORT`` - The TCP/UDP port of the registry server. The default is ``18811``.

* ``--registry-host=REGHOST`` - The host running the registry server. For UDP the default is
  broadcast (``255.255.255.255``); for TCP, this parameter is **required**.


SSL switches
^^^^^^^^^^^^
If any of the following switches is given, the server uses the SSL authenticator. These cannot be
used with conjunction with ``--vdb``.

* ``--ssl-keyfile=FILENAME`` - the server's SSL key-file. Required for SSL

* ``--ssl-certfile=FILENAME`` - the server's SSL certificate file. Required for SSL

* ``--ssl-cafile=FILENAME`` - the certificate authority chain file. This switch is optional; if
  it's given, it enables client-side authentication.


.. _custom-servers:

Custom RPyC Servers
-------------------
Starting an RPyC server that exposes your service is quite easy -- when you construct the
:class:`rpyc.utils.server.Server` instance, pass it your :class:`rpyc.core.service.Service` factory.
You can use the following snippet::

  import rpyc
  from rpyc.utils.server import ThreadedServer # or ForkingServer

  class MyService(rpyc.Service):
      #
      # ... you service's implementation
      #
      pass

  if __name__ == "__main__":
      server = ThreadedServer(MyService, port = 12345)
      server.start()

Refer to :class:`rpyc.utils.server.Server` for the list all possible arguments.

.. _registry-server:

Registry Server
---------------
RPyC comes with a simple command-line registry server, which can be configured quite extensively
by command-line switches. The registry server is a bonjour-like agent, with which services may
register and clients may perform queries. For instance, if you start an RPyC server that provides
service ``Foo`` on ``myhost:17777``, you can register that server with the registry server, which
would allow clients to later query for the servers that expose that service (and get back a list
of TCP endpoints). For more info, see :ref:`api-registry`.

Switches
^^^^^^^^
* ``-m``, ``--mode=MODE` - The registry mode; either ``UDP`` or ``TCP``. The default is ``UDP``.

* ``-p``, ``--port=PORT`` - The UDP/TCP port to bind to. The default is ``18811``.

* ``-f``, ``--file=FILE`` - The log file to use. The default is ``stderr``.

* ``-q``, ``--quiet`` - If given, sets quiet mode (only errors are logged)

* ``-t``, ``--timeout=PRUNING_TIMEOUT`` - Sets a custom pruning timeout, in seconds. The pruning
  time is the amount of time the registry server will keep a previously-registered service, when
  it no longer sends timely keepalives. The default is 4 minutes (240 seconds).






