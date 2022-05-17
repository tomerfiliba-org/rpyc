"""
An *authenticator* is basically a callable object that takes a socket and
"authenticates" it in some way. Upon success, it must return a tuple containing
a **socket-like** object and its **credentials** (any object), or raise an
:class:`AuthenticationError` upon failure. The credentials are any object you wish to
associate with the authentication, and it's stored in the connection's
:data:`configuration dict <rpyc.core.protocol.DEFAULT_CONFIG>` under the key "credentials".

There are no constraints on what the authenticators, for instance::

    def magic_word_authenticator(sock):
        if sock.recv(5) != "Ma6ik":
            raise AuthenticationError("wrong magic word")
        return sock, None

RPyC comes bundled with an authenticator for ``SSL`` (using certificates).
This authenticator, for instance, both verifies the peer's identity and wraps the
socket with an encrypted transport (which replaces the original socket).

Authenticators are used by :class:`~rpyc.utils.server.Server` to
validate an incoming connection. Using them is pretty trivial ::

    s = ThreadedServer(...., authenticator = magic_word_authenticator)
    s.start()
"""
import sys
from rpyc.lib import safe_import
ssl = safe_import("ssl")


class AuthenticationError(Exception):
    """raised to signal a failed authentication attempt"""
    pass


class SSLAuthenticator(object):
    """An implementation of the authenticator protocol for ``SSL``. The given
    socket is wrapped by ``ssl.SSLContext.wrap_socket`` and is validated based on
    certificates

    :param keyfile: the server's key file
    :param certfile: the server's certificate file
    :param ca_certs: the server's certificate authority file
    :param cert_reqs: the certificate requirements. By default, if ``ca_cert`` is
                      specified, the requirement is set to ``CERT_REQUIRED``;
                      otherwise it is set to ``CERT_NONE``
    :param ciphers: the list of ciphers to use, or ``None``, if you do not wish
                    to restrict the available ciphers. New in Python 2.7/3.2
    :param ssl_version: the SSL version to use

    Refer to `ssl.SSLContext <http://docs.python.org/dev/library/ssl.html#ssl.SSLContext>`_
    for more info.

    Clients can connect to this authenticator using
    :func:`rpyc.utils.factory.ssl_connect`. Classic clients can use directly
    :func:`rpyc.utils.classic.ssl_connect` which sets the correct
    service parameters.
    """

    def __init__(self, keyfile, certfile, ca_certs=None, cert_reqs=None,
                 ssl_version=None, ciphers=None):
        self.keyfile = str(keyfile)
        self.certfile = str(certfile)
        self.ca_certs = str(ca_certs) if ca_certs else None
        self.ciphers = ciphers
        if cert_reqs is None:
            if ca_certs:
                self.cert_reqs = ssl.CERT_REQUIRED
            else:
                self.cert_reqs = ssl.CERT_NONE
        else:
            self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version

    def __call__(self, sock):
        try:
            if self.ssl_version is None:
                context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            else:
                context = ssl.SSLContext(self.ssl_version)
            context.load_cert_chain(self.certfile, keyfile=self.keyfile)
            if self.ca_certs is not None:
                context.load_verify_locations(self.ca_certs)
            if self.ciphers is not None:
                context.set_ciphers(self.ciphers)
            if self.cert_reqs is not None:
                context.verify_mode = self.cert_reqs
            sock2 = context.wrap_socket(sock, server_side=True)
        except ssl.SSLError:
            ex = sys.exc_info()[1]
            raise AuthenticationError(str(ex))
        return sock2, sock2.getpeercert()
