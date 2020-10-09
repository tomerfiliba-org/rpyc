import rpyc
import sys
import os
import unittest
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService, MasterService


try:
    from plumbum.machines.ssh_machine import SshMachine
    localhost_machine = SshMachine("localhost")
    localhost_machine.close()
except Exception:
    localhost_machine = None


@unittest.skipIf(localhost_machine is None, "Requires paramiko_machine to localhost")
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
            cls.server._start_in_thread()
        cls.remote_machine =  SshMachine("localhost")
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
        cls.server.close()

    def test_simple(self):
        print("server's pid =", self.conn.modules.os.getpid())
        self.conn.modules.sys.stdout.write("hello over ssh\n")
        self.conn.modules.sys.stdout.flush()

    def test_connect(self):
        self.conn2.modules.sys.stdout.write("hello through rpyc.ssh_connect()\n")
        self.conn2.modules.sys.stdout.flush()


if __name__ == "__main__":
    unittest.main()
