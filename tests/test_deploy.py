from __future__ import with_statement 
import sys
import unittest
from plumbum import SshMachine
from rpyc.utils.zerodeploy import DeployedServer

class TestDeploy(unittest.TestCase):
    def test_deploy(self):
        rem = SshMachine("localhost")
        with DeployedServer(rem) as dep:
            conn = dep.classic_connect()
            print (conn.modules.sys)
            func = conn.modules.os.getcwd
            print (func())
        
        try:
            func()
        except EOFError:
            pass
        else:
            self.fail("expected an EOFError")
    
    def test_deploy_paramiko(self):
        try:
            import paramiko     # @UnusedImport
        except Exception:
            self.skipTest("Paramiko is not available")
        from plumbum.machines.paramiko_machine import ParamikoMachine
        
        rem = ParamikoMachine("localhost")
        with DeployedServer(rem) as dep:
            conn = dep.classic_connect()
            print (conn.modules.sys)
            func = conn.modules.os.getcwd
            print (func())


if __name__ == "__main__":
    unittest.main()
