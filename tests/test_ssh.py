import rpyc
import time
import sys
import os
import unittest
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService, MasterService


ssh_opts = ("-o", "PasswordAuthentication=no")
try:
    from plumbum.machines.ssh_machine import SshMachine
    localhost_machine = SshMachine("localhost", ssh_opts=ssh_opts)
    localhost_machine.close()
except Exception:
    localhost_machine = None

@unittest.skipIf(localhost_machine is None, "Requires SshMachine to localhost")
class Test_Ssh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform == "win32":
            cls.server = None
            os.environ["HOME"] = os.path.expanduser("~")
        else:
            # assume "ssh localhost" is configured to run without asking for password
            # `.ssh/config`
            # Host localhost
            #   HostName 127.0.0.1
            #   User <username>
            #   IdentityFile <id_rsa>
            cls.server = ThreadedServer(SlaveService, hostname="localhost",
                                        ipv6=False, port=18888, auto_register=False)
            cls.thd = cls.server._start_in_thread()
        cls.remote_machine = SshMachine("localhost", ssh_opts=ssh_opts)
        cls.conn = rpyc.classic.ssh_connect(cls.remote_machine, 18888)
        cls.conn2 = rpyc.ssh_connect(cls.remote_machine, 18888, service=MasterService)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.conn2.close()
        # TODO review "ResourceWarning: subprocess 111785 is still running"
        cls.remote_machine._session.proc.terminate()  # fix resource warning
        cls.remote_machine._session.proc.communicate()  # fix resource warning
        cls.remote_machine.close()
        if cls.server is not None:
            while cls.server.clients:
                time.sleep(0.250)
            cls.server.close()
            cls.thd.join()

    def test_simple(self):
        print("server's pid =", self.conn.modules.os.getpid())
        self.conn.modules.sys.stdout.write("hello over ssh\n")
        self.conn.modules.sys.stdout.flush()

    def test_connect(self):
        self.conn2.modules.sys.stdout.write("hello through rpyc.ssh_connect()\n")
        self.conn2.modules.sys.stdout.flush()


if __name__ == "__main__":
    unittest.main()
