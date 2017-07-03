.. _ssl:

SSL
===
Python 2.6 introduced the ``ssl`` module, and RPyC can now integrate with it.
If you wish to use ``ssl`` on versions earlier than Python 2.6, see the
:ref:`ssl-wrapper <dependencies>`.

Using external tools, you can generate client and server certificates, and a certificate
authority. After going through this setup stage, you can easily establish an SSL-enabled
connection.

Server side::

    from rpyc.utils.authenticators import SSLAuthenticator
    from rpyc.utils.server import ThreadedServer

    # ...

    authenticator = SSLAuthenticator("myserver.key", "myserver.cert")
    server = ThreadedServer(SlaveService, port = 12345, authenticator = authenticator)
    server.start()

Client side::

    import rpyc

    conn = rpyc.ssl_connect("hostname", port = 12345, keyfile="client.key",
                            certfile="client.cert")

For more info, see the documentation of `ssl module <http://docs.python.org/library/ssl.html>`_.


.. _ssh-tunneling:

SSH Tunneling
=============
SSL is a bit too complicated: you must generate certificates for each client and server,
sign them, manage the CA chains, etc. It's usually an overkill for the normal use-case of RPyC.
Instead, SSH offers a much easier approach. Conceptually, SSH is similar to SSL, but requires
considerably less setup: once two machines are acquainted, you can easily set the trust-relations
between them using the ``authorized_keys`` and ``known_hosts`` configuration files. You can
also use interactive password authentication, in case it's desired.

SSH is first-and-foremost a shell-protocol, but it includes **tunneling** support. This means
you can route "unaware" connections over a tunnel, and get encryption and authentication for
free. Setting up tunnels is not at all complicated, but in order to make life even easier,
RPyC comes bundled with SSH-tunneling support (of course you'll need an SSH client installed
and configured, in order to use it).

Usage
-----
In order to use the built-in SSH tunneling support, you'll first have to start a server on you
host, binding the server to the ``localhost`` on some port, say 12345. Binding the server to
the ``localhost`` means that the server cannot accept external connections -- which is crucial
for our security scheme.

Next, from your client machine, you'll create an :class:`SshContext <rpyc.utils.ssh.SshContext>`.
The context object holds all the information required to establish an SSH connection from your
client machine to the host machine -- host name, port, user name, keyfile, SSH program, etc.
If the two machines are "acquainted" and your ``ssh/config`` is set up accordingly, the context
can be pretty much empty, as all the required information already exists. If not, you'll need
to include this information programmatically, like so::

    from rpyc.utils.ssh import SshContext

    sshctx = SshContext("myserver", user = "foo", keyfile = r"/path/to/my/keyfile")

And then, establishing a connection over SSH is a one-liner:

    conn = rpyc.ssh_connect(sshctx, 12345)

When establishing the connection, RPyC will first set up an SSH tunnel from your client
machine to the host machine, using the credentials given by the ``SshContext``, and then use
this tunnel to create the actual RPyC connection.

The tunneled-connection consists of three parts:

* A socket from port X on the client machine (the RPyC client) to port Y on the client machine
  (first side of the tunnel)

* A socket from port Y on the client machine (the first side of the tunnel) to port Z on the
  server machine (second side of the tunnel) -- this is the encrypted connection.

* A socket from port Z on the server machine (the second side of the tunnel) to port W on the
  server machine (the RPyC server itself)

And RPyC makes the necessary arrangements to hide these details from you.



