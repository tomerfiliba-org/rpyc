.. _ssl:

SSL
===
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
