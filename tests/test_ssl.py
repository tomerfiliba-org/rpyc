import rpyc
import os
import time
import unittest
from rpyc.utils.authenticators import SSLAuthenticator
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService

try:
    import ssl  # noqa
    _ssl_import_failed = False
except ImportError:
    _ssl_import_failed = True

sslport=18812

class Authenticator(SSLAuthenticator):
    def __call__(self, sock):
        time.sleep(0.25)
        return super().__call__(sock)

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

        authenticator = Authenticator(cls.key, cls.cert, cls.ca_certs)
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
                                     keyfile=self.client_key, certfile=self.client_cert)
        print(repr(c))
        print(c.modules.sys)
        print(c.modules["xml.dom.minidom"].parseString("<a/>"))
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()

    def test_client2(self):
        '''Assert exception client signed client2, but being in ca bundle is not server signature'''
        with self.assertRaisesRegex(EOFError, 'tlsv[0-9]* alert unknown ca'):
            c = rpyc.classic.ssl_connect("localhost", port=sslport,
                                         keyfile=self.client2_key, certfile=self.client2_cert)
            c.close()

    def test_nokey(self):
        '''Assert exception when cert not provided'''
        with self.assertRaisesRegex(EOFError, 'tlsv[0-9]* alert certificate required'):
            c = rpyc.classic.ssl_connect("localhost", port=sslport)
            c.close()


@unittest.skipIf(_ssl_import_failed, "Ssl not available")
class Test_SSL_CERT_REQUIRED(unittest.TestCase):
    '''It may be nonobvious and easy to misconfigure, but not specify'''
    @classmethod
    def setUpClass(cls):
        cls.key = os.path.join(os.path.dirname(__file__), "server.key")
        cls.cert = os.path.join(os.path.dirname(__file__), "server.crt")
        print(cls.cert, cls.key)

        authenticator = Authenticator(cls.key, cls.cert, cert_reqs=ssl.CERT_REQUIRED)
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
        with self.assertRaisesRegex(EOFError, 'tlsv[0-9]* alert certificate required'):
            c = rpyc.classic.ssl_connect("localhost", port=sslport)
            c.close()


@unittest.skipIf(_ssl_import_failed, "Ssl not available")
class Test_SSL_CERT_NONE(unittest.TestCase):
    '''It may be nonobvious and easy to misconfigure, but not specify'''
    @classmethod
    def setUpClass(cls):
        cls.key = os.path.join(os.path.dirname(__file__), "server.key")
        cls.cert = os.path.join(os.path.dirname(__file__), "server.crt")
        print(cls.cert, cls.key)

        authenticator = Authenticator(cls.key, cls.cert)
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
        c = rpyc.classic.ssl_connect("localhost", port=sslport)
        c.close()


if __name__ == "__main__":
    unittest.main()
