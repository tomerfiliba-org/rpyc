from __future__ import with_statement
import unittest
import sys
from plumbum import SshMachine
from plumbum.machines.paramiko_machine import ParamikoMachine
from rpyc.utils.zerodeploy import DeployedServer
try:
    import paramiko  # noqa
    _paramiko_import_failed = False
except Exception:
    _paramiko_import_failed = True


@unittest.skipIf(_paramiko_import_failed, "Paramiko is not available")
class TestDeploy(unittest.TestCase):
    def test_deploy(self):
        rem = SshMachine("localhost")
        SshMachine.python = rem[sys.executable]
        with DeployedServer(rem) as dep:
            conn = dep.classic_connect()
            print(conn.modules.sys)
            func = conn.modules.os.getcwd
            print(func())

        try:
            func()
        except EOFError:
            pass
        else:
            self.fail("expected an EOFError")

    def test_deploy_paramiko(self):
        rem = ParamikoMachine("localhost", missing_host_policy=paramiko.AutoAddPolicy())
        with DeployedServer(rem) as dep:
            conn = dep.classic_connect()
            print(conn.modules.sys)
            func = conn.modules.os.getcwd
            print(func())

        try:
            func()
        except EOFError:
            pass
        else:
            self.fail("expected an EOFError")


if __name__ == "__main__":
    unittest.main()
