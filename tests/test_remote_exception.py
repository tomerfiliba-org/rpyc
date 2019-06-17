from __future__ import with_statement
import rpyc
import unittest


class MyService(rpyc.Service):

    def exposed_set_version(self):
        rpyc.version.version_string = '1.0.0'

    def exposed_remote_assert(self, val):
        assert val


class TestRemoteException(unittest.TestCase):
    def setUp(self):
        self.server = rpyc.utils.server.OneShotServer(MyService, port=0)
        self.server.logger.quiet = False
        self.server._start_in_thread()
        self.original_version_string = rpyc.version.version_string
        self.conn = rpyc.connect("localhost", port=self.server.port)

    def tearDown(self):
        rpyc.version.version_string = self.original_version_string
        self.conn.close()

    def test_remote_exception(self):
        # Since the server/client share the same namespace, the version will change for both.
        # Even so, this should suffice for unit testing
        warn_msg = 'WARNING: Remote is on RPyC 1.0.0 and local is on RPyC 1.0.0.'
        try:
            self.conn.root.remote_assert(False)
        except Exception as exc:
            exc_rpyc_version = exc._remote_version
            exc_remote_tb = exc._remote_tb
        else:
            exc_rpyc_version = None
            exc_remote_tb = ''
        self.assertEqual(self.original_version_string, exc_rpyc_version)
        self.assertFalse(warn_msg in exc_remote_tb)
        try:
            self.conn.root.set_version()
            self.conn.root.remote_assert(False)
        except Exception as exc:
            exc_rpyc_version = exc._remote_version
            exc_remote_tb = exc._remote_tb
        else:
            exc_rpyc_version = None
            exc_remote_tb = ''
        self.assertEqual('1.0.0', exc_rpyc_version)
        self.assertTrue(warn_msg in exc_remote_tb)


class TestExclusionsRemoteException(unittest.TestCase):
    def setUp(self):
        config = {'include_local_traceback': False, 'include_local_version': False}
        self.server = rpyc.utils.server.OneShotServer(MyService, port=0, protocol_config=config)
        self.server.logger.quiet = False
        self.server._start_in_thread()
        self.conn = rpyc.connect("localhost", port=self.server.port)

    def tearDown(self):
        self.conn.close()

    def test_remote_exception(self):
        try:
            self.conn.root.remote_assert(False)
        except Exception as exc:
            exc_rpyc_version = exc._remote_version
            exc_remote_tb = exc._remote_tb
        else:
            exc_rpyc_version = None
            exc_remote_tb = ''
        self.assertEqual("<traceback denied>", exc_remote_tb)
        self.assertEqual("<version denied>", exc_rpyc_version)


if __name__ == "__main__":
    unittest.main()
