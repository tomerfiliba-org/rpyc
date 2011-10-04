import rpyc
import time
import threading
import sys
import unittest
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
from rpyc.utils.ssh import SshContext


class Test_Ssh(unittest.TestCase):
    def setUp(self):
        # setup an SSH context. on linux this would be as simple as
        # sshctx = SshContext("myhost")
        # assuming your user is configured to connect using authorized_keys
        
        if sys.platform == "win32":
            # on my windows box, it's a little more complicated:
            self.server = None
            sshctx = SshContext("hollywood.xiv.ibm.com", ssh_program = r"c:\Program Files\Git\bin\ssh.exe",
                user = "tomer", keyfile = r"c:\users\sebulba\.ssh\id_rsa")
            # make sure a classic server is running on remote-host:18888
            self.conn = rpyc.classic.ssh_connect(sshctx, "18888")
        else:
            # assume "ssh localhost" is configured to run without asking for password 
            self.server = ThreadedServer(SlaveService, hostname = "localhost", 
                ipv6 = False, port = 0, auto_register=False)
            t = threading.Thread(target=self.server.start)
            t.setDaemon(True)
            t.start()
            time.sleep(0.5)
            self.sshctx = SshContext("localhost")
            self.conn = rpyc.classic.ssh_connect(self.sshctx, self.server.port)

    def tearDown(self):
        self.conn.close()
        if self.server:
            self.server.close()

    def test_simple(self):
        print( "server's pid =", self.conn.modules.os.getpid())
        self.conn.modules.sys.stdout.write("hello over ssh\n")
        self.conn.modules.sys.stdout.flush()

    def test_connect(self):
        conn2 = rpyc.ssh_connect(self.sshctx, self.server.port, 
                                 service=SlaveService)
        conn2.modules.sys.stdout.write("hello through rpyc.ssh_connect()\n")
        conn2.modules.sys.stdout.flush()

if __name__ == "__main__":
    unittest.main()


