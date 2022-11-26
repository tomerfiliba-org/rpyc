from __future__ import with_statement

import unittest
import subprocess
import sys

from plumbum import SshMachine
from plumbum.machines.paramiko_machine import ParamikoMachine
from rpyc.utils.zerodeploy import DeployedServer
try:
    import paramiko  # noqa
    _paramiko_import_failed = False
except Exception:
    _paramiko_import_failed = True


class TestDeploy(unittest.TestCase):
    def test_deploy(self):
        rem = SshMachine("localhost")
        SshMachine.python = rem[sys.executable]
        with DeployedServer(rem) as dep:
            conn = dep.classic_connect()
            print(conn.modules.sys)
            func = conn.modules.os.getcwd
            print(func())
            conn.close()

        try:
            func()
        except EOFError:
            pass
        else:
            self.fail("expected an EOFError")
        rem.close()

    def test_close_timeout(self):
        expected_timeout = 4
        observed_timeouts = []
        original_communicate = subprocess.Popen.communicate

        def replacement_communicate(self, input=None, timeout=None):
            observed_timeouts.append(timeout)
            return original_communicate(self, input, timeout)

        try:
            subprocess.Popen.communicate = replacement_communicate
            rem = SshMachine("localhost")
            SshMachine.python = rem[sys.executable]
            dep = DeployedServer(rem)
            conn = dep.classic_connect()
            dep.close(timeout=expected_timeout)
            rem.close()
            conn.close()
        finally:
            subprocess.Popen.communicate = original_communicate
        # The last three calls to communicate() happen during close(), so check they
        # applied the timeout.
        self.assertEqual(observed_timeouts[-3:], [expected_timeout] * 3)

    def test_close_timeout_default_none(self):
        observed_timeouts = []
        original_communicate = subprocess.Popen.communicate

        def replacement_communicate(self, input=None, timeout=None):
            observed_timeouts.append(timeout)
            return original_communicate(self, input, timeout)

        try:
            subprocess.Popen.communicate = replacement_communicate
            rem = SshMachine("localhost")
            SshMachine.python = rem[sys.executable]
            dep = DeployedServer(rem)
            conn = dep.classic_connect()
            dep.close()
            rem.close()
            conn.close()
        finally:
            subprocess.Popen.communicate = original_communicate
        # No timeout specified, so Popen.communicate should have been called with timeout None.
        self.assertEqual(observed_timeouts, [None] * len(observed_timeouts))

    @unittest.skipIf(_paramiko_import_failed, "Paramiko is not available")
    def test_deploy_paramiko(self):
        rem = ParamikoMachine("localhost", missing_host_policy=paramiko.AutoAddPolicy())
        with DeployedServer(rem) as dep:
            conn = dep.classic_connect()
            print(conn.modules.sys)
            func = conn.modules.os.getcwd
            print(func())
            conn.close()

        try:
            func()
        except EOFError:
            pass
        else:
            self.fail("expected an EOFError")
        rem.close()


if __name__ == "__main__":
    unittest.main()
