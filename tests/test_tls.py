import thread, time

from nose.tools import raises

import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc.utils.authenticators import TlsliteVdbAuthenticator
import rpyc
import thread, time
try:
    from tlslite.api import TLSError
except ImportError:
    print "Couldn't tlslite.api "
    class TLSError(Exception):
        def __init__(self):
            self.value = "My own TLSError"
        def __str__(self):
            return repr(self.value)


#TODO: rename to Test_ when those are working            
class Tlslite(object):
    def setup(self):
        if TLSError is None:
            self.cannot_run("this test requires tlslite be installed")
        
        users = {
            "foo" : "bar",
            "spam" : "eggs",
        }
        authenticator = TlsliteVdbAuthenticator.from_dict(users)
        self.server = ThreadedServer(rpyc.SlaveService, hostname = "localhost", 
            authenticator = authenticator)
        self.server.logger.quiet = True
        thread.start_new(self.server.start, ())
        time.sleep(1) # make sure the server has initialized, etc.
    
    def teardown(self):
        self.server.close()
    
    def test_successful(self):
        c = rpyc.classic.tls_connect("localhost", "spam", "eggs", 
            port = self.server.port)
        self.log("server credentials = %r", c.root.getconn()._config["credentials"])
        self.log("%s", c.modules.sys)
        c.close()
    
    def _expect_fail(self, username, password):
        self.log("expecting %s:%s to fail", username, password)
        try:
            c = rpyc.classic.tlslite_connect("localhost", username, password, 
                port = self.server.port)
        except:
            raise TLSError()
        else:
            print "nothing failed ???? WTF"

    @raises(TLSError)                                    #Maybe need a name here
    def test_wrong_tokens(self):
        self._expect_fail("spam", "bar")

    @raises(TLSError)                                    #Maybe need a name here
    def test_wrong_tokens2(self):
        self._expect_fail("bloop", "blaap")

    
