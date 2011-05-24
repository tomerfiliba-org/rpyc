import rpyc
import time
import threading
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
from rpyc.utils.ssh import SshContext


class Test_Ssh(object):
    def setup(self):
        # setup an SSH context. on linux this would be as simple as
        # sshctx = SshContext("myhost")
        # assuming your user is configured to connect using authorized_keys
        # on my windows box, it's a little more complicated:
        #
        # sshctx = SshContext("hollywood.xiv.ibm.com", ssh_program = r"c:\Program Files\Git\bin\ssh.exe",
        #    user = "tomer", keyfile = r"c:\users\sebulba\.ssh\id_rsa")
        # 
        #make sure a classic server is running on remote-host:18888, e.g.
        # proc = sshctx.popen("python", "rpyc_classic.py", "--host=localhost", "--port=18888")

        # assume "ssh localhost" is configured to run without asking for password 
        self.server = ThreadedServer(SlaveService, hostname = "localhost", 
            ipv6 = False, port = 19999, auto_register=False)
        t = threading.Thread(target=self.server.start)
        t.start()
        time.sleep(0.5)
        sshctx = SshContext("localhost")
        self.conn = rpyc.classic.ssh_connect(sshctx, 19999)

    def teardown(self):
        self.conn.close()
        self.server.close()

    def test_simple(self):
        print "server's pid =", self.conn.modules.os.getpid()
        self.conn.modules.sys.stdout.write("hello over ssh\n")
        self.conn.modules.sys.stdout.flush()

