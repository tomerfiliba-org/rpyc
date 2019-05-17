import rpyc
import time
import sys
import os
import unittest
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService, MasterService
from plumbum import SshMachine


class Test_Ssh(unittest.TestCase):
    def setUp(self):
        if sys.platform == "win32":
            self.server = None
            os.environ["HOME"] = os.path.expanduser("~")
            self.remote_machine = SshMachine("localhost")
        else:
            # assume "ssh localhost" is configured to run without asking for password
            # `.ssh/config`
            # Host localhost
            #   HostName 127.0.0.1
            #   User <username>
            #   IdentityFile <id_rsa>
            self.server = ThreadedServer(SlaveService, hostname = "localhost",
                ipv6 = False, port = 18888, auto_register=False)
            self.server._start_in_thread()
            self.remote_machine = SshMachine("localhost")

    def tearDown(self):
        if self.server:
            self.server.close()

    def test_simple(self):
        conn = rpyc.classic.ssh_connect(self.remote_machine, 18888)
        print( "server's pid =", conn.modules.os.getpid())
        conn.modules.sys.stdout.write("hello over ssh\n")
        conn.modules.sys.stdout.flush()

    def test_connect(self):
        conn2 = rpyc.ssh_connect(self.remote_machine, 18888, service=MasterService)
        conn2.modules.sys.stdout.write("hello through rpyc.ssh_connect()\n")
        conn2.modules.sys.stdout.flush()

if __name__ == "__main__":
    unittest.main()
