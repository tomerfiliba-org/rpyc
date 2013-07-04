import rpyc
import os
import threading
import unittest
import time
from rpyc.utils.authenticators import SSLAuthenticator
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
from nose import SkipTest

try:
    import ssl #@UnusedImport
except ImportError:
    raise SkipTest("requires ssl")


class Test_SSL(unittest.TestCase):
    '''
    created key like that
    http://www.akadia.com/services/ssh_test_certificate.html

    openssl req -newkey rsa:1024 -nodes -keyout mycert.pem -out mycert.pem
    '''

    def setUp(self):
        self.key = os.path.join( os.path.dirname(__file__) , "server.key")
        self.cert =  os.path.join( os.path.dirname(__file__) , "server.crt")
        print( self.cert, self.key )

        authenticator = SSLAuthenticator(self.key, self.cert)
        self.server = ThreadedServer(SlaveService, port = 18812,
            auto_register=False, authenticator = authenticator)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        time.sleep(1)

    def tearDown(self):
        self.server.close()

    def test_ssl_conenction(self):
        c = rpyc.classic.ssl_connect("localhost", port = 18812,
            keyfile=self.key, certfile=self.cert)
        print( repr(c) )
        print( c.modules.sys )
        print( c.modules["xml.dom.minidom"].parseString("<a/>") )
        c.execute("x = 5")
        self.assertEqual(c.namespace["x"], 5)
        self.assertEqual(c.eval("1+x"), 6)
        c.close()

if __name__ == "__main__":
    unittest.main()

