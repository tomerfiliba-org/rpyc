from testbase import TestBase
from rpyc.utils.server import ThreadedServer
from rpyc.utils.authenticators import VdbAuthenticator
import rpyc
import thread, time
try:
    from tlslite.api import TLSError
except ImportError:
    TLSError = None


class Tlslite(TestBase):
    def setup(self):
        if TLSError is None:
            self.cannot_run("this test requires win32")
        
        users = {
            "foo" : "bar",
            "spam" : "eggs",
        }
        authenticator = VdbAuthenticator.from_users(users)
        self.server = ThreadedServer(rpyc.SlaveService, hostname = "localhost", 
            authenticator = authenticator)
        self.server.logger.quiet = True
        thread.start_new(self.server.start, ())
        time.sleep(1) # make sure the server has initialized, etc.
    
    def cleanup(self):
        self.server.close()
    
    def step_successful(self):
        c = rpyc.classic.tls_connect("localhost", "spam", "eggs", 
            port = self.server.port)
        self.log("server credentials = %r", c.root.getconn()._config["credentials"])
        self.log("%s", c.modules.sys)
        c.close()
    
    def _expect_fail(self, username, password):
        self.log("expecting %s:%s to fail", username, password)
        try:
            c = rpyc.classic.tls_connect("localhost", username, password, 
                port = self.server.port)
        except TLSError:
            pass
        else:
            self.fail("expected authentication to fail")
    
    def step_wrong_tokens(self):
        self._expect_fail("spam", "bar")
        self._expect_fail("bloop", "blaap")

    
if __name__ == "__main__":
    Tlslite.run()

