import rpyc
import os
import time
import sys
import socket
import unittest
from rpyc.utils.authenticators import AuthenticationError
from rpyc.utils.server import ThreadedServer
from rpyc.core.consts import STREAM_CHUNK
from rpyc import SlaveService

try:
    import ssl  # noqa
    _ssl_import_failed = False
except ImportError:
    _ssl_import_failed = True

sslport=18812


class SSLServerAuthenticator:
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

    Refer to `ssl.SSLContext <https://docs.python.org/dev/library/ssl.html#ssl.SSLContext>`_
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
            sock2 = context.wrap_socket(sock, do_handshake_on_connect=False, server_side=True)
            try:
                sock2.do_handshake()
            except Exception:
                # exception during connection setup
                # enforce client side to close connection first
                sock3 = socket.socket(fileno=sock2.detach())
                while True:
                    buf = sock3.recv(STREAM_CHUNK)
                    if not buf:
                        break
                sock3.close()
                raise
        except ssl.SSLError:
            ex = sys.exc_info()[1]
            raise AuthenticationError(str(ex))
        return sock2, sock2.getpeercert()


@unittest.skipIf(_ssl_import_failed, "Ssl not available")
class Test_SSL(unittest.TestCase):
    '''Created keys/certs like https://gist.github.com/soarez/9688998
    # Server key
    openssl genrsa -out server.key 4096
    openssl req -new -x509 -key server.key -out server.crt
    # Client key
    openssl genrsa -out client.key 4096
    openssl req -new -key client.key -out client.csr
    openssl x509 -req -in  client.csr  -CA server.crt -CAkey server.key -out client.crt
    # Client2 key
    openssl genrsa -out client2.key 4096
    openssl req -new -key client2.key -out client2.csr
    openssl x509 -req -in  client2.csr  -CA client.crt -CAkey client.key -out client2.crt
    # Create bundle
    cat client.crt server.crt > client-server.bundle.crt
    '''

    @classmethod
    def setUpClass(cls):
        cls.key = os.path.join(os.path.dirname(__file__), "server.key")
        cls.cert = os.path.join(os.path.dirname(__file__), "server.crt")
        cls.client_key = os.path.join(os.path.dirname(__file__), "client.key")
        cls.client_cert = os.path.join(os.path.dirname(__file__), "client.crt")
        cls.client2_key = os.path.join(os.path.dirname(__file__), "client2.key")
        cls.client2_cert = os.path.join(os.path.dirname(__file__), "client2.crt")
        cls.ca_certs = os.path.join(os.path.dirname(__file__), "client-server.bundle.crt")
        print(cls.cert, cls.key)

        authenticator = SSLServerAuthenticator(cls.key, cls.cert, cls.ca_certs, ssl_version=ssl.PROTOCOL_TLS_SERVER)
        cls.server = ThreadedServer(SlaveService, port=sslport,
                                     auto_register=False, authenticator=authenticator)
        cls.server.logger.quiet = False
        cls.thd = cls.server._start_in_thread()

    @classmethod
    def tearDownClass(cls):
        while cls.server.clients:
            pass
        cls.server.close()
        cls.thd.join()

    def test_client(self):
        c = rpyc.classic.ssl_connect("localhost", port=sslport,
                                     ssl_version=ssl.PROTOCOL_TLS_CLIENT,
                                     keyfile=self.client_key, certfile=self.client_cert,
                                     ca_certs=self.ca_certs)
        print(repr(c))
        print(c.modules.sys)
        print(c.modules["xml.dom.minidom"].parseString("<a/>"))
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()

    def test_client2(self):
        '''Assert exception client signed client2, but being in ca bundle is not server signature'''
        with self.assertRaisesRegex(EOFError,
                                    'tlsv[0-9]* alert unknown ca'):
            c = rpyc.classic.ssl_connect("localhost", port=sslport,
                                         ssl_version=ssl.PROTOCOL_TLS_CLIENT,
                                         keyfile=self.client2_key, certfile=self.client2_cert, ca_certs=self.ca_certs)
            c.close()

    def test_nokey(self):
        '''Assert exception when cert not provided'''
        with self.assertRaisesRegex(EOFError,
                                    'tlsv[0-9]* alert certificate required'):
            c = rpyc.classic.ssl_connect("localhost", port=sslport,
                                         ssl_version=ssl.PROTOCOL_TLS_CLIENT,
                                         ca_certs=self.ca_certs)
            c.close()


@unittest.skipIf(_ssl_import_failed, "Ssl not available")
class Test_SSL_CERT_REQUIRED(unittest.TestCase):
    '''It may be nonobvious and easy to misconfigure, but not specify'''
    @classmethod
    def setUpClass(cls):
        cls.key = os.path.join(os.path.dirname(__file__), "server.key")
        cls.cert = os.path.join(os.path.dirname(__file__), "server.crt")
        cls.ca_certs = os.path.join(os.path.dirname(__file__), "client-server.bundle.crt")
        print(cls.cert, cls.key)

        authenticator = SSLServerAuthenticator(cls.key, cls.cert, cert_reqs=ssl.CERT_REQUIRED)
        cls.server = ThreadedServer(SlaveService, port=sslport,
                                     auto_register=False, authenticator=authenticator)
        cls.server.logger.quiet = False
        cls.thd = cls.server._start_in_thread()

    @classmethod
    def tearDownClass(cls):
        while cls.server.clients:
            pass
        cls.server.close()
        cls.thd.join()

    def test_nokey(self):
        '''Assert exception when cert not provided'''
        with self.assertRaisesRegex(EOFError,
                                    'tlsv[0-9]* alert certificate required'):
            c = rpyc.classic.ssl_connect("localhost", port=sslport,
                                         ssl_version=ssl.PROTOCOL_TLS_CLIENT,
                                         ca_certs=self.ca_certs)
            c.close()


@unittest.skipIf(_ssl_import_failed, "Ssl not available")
class Test_SSL_CERT_NONE(unittest.TestCase):
    '''It may be nonobvious and easy to misconfigure, but not specify'''
    @classmethod
    def setUpClass(cls):
        cls.key = os.path.join(os.path.dirname(__file__), "server.key")
        cls.cert = os.path.join(os.path.dirname(__file__), "server.crt")
        cls.ca_certs = os.path.join(os.path.dirname(__file__), "client-server.bundle.crt")
        print(cls.cert, cls.key)

        authenticator = SSLServerAuthenticator(cls.key, cls.cert)
        cls.server = ThreadedServer(SlaveService, port=sslport,
                                     auto_register=False, authenticator=authenticator)
        cls.server.logger.quiet = False
        cls.thd = cls.server._start_in_thread()

    @classmethod
    def tearDownClass(cls):
        while cls.server.clients:
            pass
        cls.server.close()
        cls.thd.join()

    def test_nokey_noexc(self):
        c = rpyc.classic.ssl_connect("localhost", port=sslport,
                                     ssl_version=ssl.PROTOCOL_TLS_CLIENT,
                                     ca_certs=self.ca_certs)
        c.close()


if __name__ == "__main__":
    unittest.main()
