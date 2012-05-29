from __future__ import with_statement 
import sys
import unittest
from plumbum import SshMachine
from rpyc.utils.zerodeploy import deployment

class TestDeploy(unittest.TestCase):
    def test_deploy(self):
        rem = SshMachine("localhost")
        SshMachine.python = rem[sys.executable]  # major hack
        with deployment(rem) as dep:
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


if __name__ == "__main__":
    unittest.main()
