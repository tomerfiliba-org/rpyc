import unittest
from plumbum import SshMachine
from rpyc.utils.zerodeploy import deployment

class TestDeploy(unittest.TestCase):
    def test_deploy(self):
        rem = SshMachine("localhost")
        with deployment(rem) as dep:
            conn = dep.classic_connect()
            print conn.modules.sys
            func = conn.modules.os.getcwd
            print func()
        
        self.assertRaises(EOFError, func)


if __name__ == "__main__":
    unittest.main()
