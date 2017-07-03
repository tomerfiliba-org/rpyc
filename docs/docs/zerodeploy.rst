.. _zerodeploy:

Zero-Deploy RPyC
================

Setting up and managing servers is a headache. You need to start the server process, monitor it throughout its
life span, make sure it doesn't hog up memory over time (or restart it if it does), make sure it comes up
automatically after reboots, manage user permissions and make sure everything remains secure. Enter zero-deploy.

Zero-deploy RPyC does all of the above, but doesn't stop there: it allows you to dispatch an RPyC server on a machine
that doesn't have RPyC installed, and even allows multiple instances of the server (each of a different port),
while keeping it all 100% secure. In fact, because of the numerous benefits of zero-deploy, it is now considered
the preferred way to deploy RPyC.

How It Works
------------

Zero-deploy only requires that you have `Plumbum <http://plumbum.readthedocs.org>`_ (1.2 and later) installed on
your client machine and that you can connect to the remote machine over SSH. It takes care of the rest:

1. Create a temporary directory on the remote machine
2. Copy the RPyC distribution (from the local machine) to that temp directory
3. Create a server file in the temp directory and run it (over SSH)
4. The server binds to an arbitrary port (call it *port A*) on the ``localhost`` interfaces of the remote
   machine, so it will only accept in-bound connections
5. The client machine sets up an SSH tunnel from a local port, *port B*, on the ``localhost`` to *port A* on the
   remote machine.
6. The client machine can now establish secure RPyC connections to the deployed server by connecting to
   ``localhost``:*port B* (forwarded by SSH)
7. When the deployment is finalized (or when the SSH connection drops for any reason), the deployed server will
   remove the temporary directory and shut down, leaving no trace on the remote machine

Usage
-----

There's a lot of detail here, of course, but the good thing is you don't have to bend your head around it --
it requires only two lines of code::

    from rpyc.utils.zerodeploy import DeployedServer
    from plumbum import SshMachine

    # create the deployment
    mach = SshMachine("somehost", user="someuser", keyfile="/path/to/keyfile")
    server = DeployedServer(mach)

    # and now you can connect to it the usual way
    conn1 = server.classic_connect()
    print conn1.modules.sys.platform

    # you're not limited to a single connection, of course
    conn2 = server.classic_connect()
    print conn2.modules.os.getpid()

    # when you're done - close the server and everything will disappear
    server.close()

The ``DeployedServer`` class can be used as a context-manager, so you can also write::

    with DeployedServer(mach) as server:
        conn = server.classic_connect()
        # ...

Here's a capture of the interactive prompt:

    >>> sys.platform
    'win32'
    >>>
    >>> mach = SshMachine("192.168.1.100")
    >>> server = DeployedServer(mach)
    >>> conn = server.classic_connect()
    >>> conn.modules.sys.platform
    'linux2'
    >>> conn2 = server.classic_connect()
    >>> conn2.modules.os.getpid()
    8148
    >>> server.close()
    >>> conn2.modules.os.getpid()
    Traceback (most recent call last):
       ...
    EOFError

You can deploy multiple instances of the server (each will live in a separate temporary directory), and create
multiple RPyC connections to each. They are completely isolated from each other (up to the fact you can use
them to run commands like ``ps`` to learn about their neighbors).

MultiServerDeployment
---------------------
If you need to deploy on a group of machines a cluster of machines, you can also use ``MultiServerDeployment``::

    from rpyc.utils.zerodeploy import MultiServerDeployment

    m1 = SshMachine("host1")
    m2 = SshMachine("host2")
    m3 = SshMachine("host3")

    dep = MultiServerDeployment([m1, m2, m3])
    conn1, conn2, conn3 = dep.classic_connect_all()

    # ...

    dep.close()

On-Demand Servers
-----------------
Zero-deploy is ideal for use-once, on-demand servers. For instance, suppose you need to connect to one of your
machines periodically or only when a certain event takes place. Keeping an RPyC server up and running at all times
is a waste of memory and a potential security hole. Using zero-deploy on demand is the best approach for
such scenarios.

Security
--------
Zero-deploy relies on SSH for security, in two ways. First, SSH authenticates the user and runs the RPyC server
under the user's permissions. You can connect as an unprivileged user to make sure strayed RPyC processes can't
``rm -rf /``. Second, it creates an SSH tunnel for the transport, so everything is kept encrypted on the wire.
And you get these features for free -- just configuring SSH accounts will do.


