import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc.utils.authenticators import TlsliteVdbAuthenticator
import thread, time
from nose.tools import raises
from nose import SkipTest

try:
    from tlslite.api import TLSError
except ImportError:
    raise SkipTest("tlslite not installed")

users = {
    "foo" : "bar",
    "spam" : "eggs",
}

class Test_tlslite(object):
    def setup(self):
        authenticator = TlsliteVdbAuthenticator.from_dict(users)
        self.server = ThreadedServer(rpyc.SlaveService, hostname = "localhost",
            authenticator = authenticator, auto_register = False)
        self.server.logger.quiet = True
        thread.start_new(self.server.start, ())
        time.sleep(1) # make sure the server has initialized, etc.

    def teardown(self):
        self.server.close()

    def test_successful(self):
        c = rpyc.classic.tlslite_connect("localhost", "spam", "eggs",
            port = self.server.port)
        print ("server credentials = %r" % (c.root.getconn()._config["credentials"],))
        print (c.modules.sys)
        c.close()

    def _expect_fail(self, username, password):
        print ("expecting %s:%s to fail" % (username, password))
        c = rpyc.classic.tlslite_connect("localhost", username, password,
            port = self.server.port)

    @raises(TLSError)
    def test_wrong_tokens(self):
        self._expect_fail("spam", "bar")

    @raises(TLSError)
    def test_wrong_tokens2(self):
        self._expect_fail("bloop", "blaap")

