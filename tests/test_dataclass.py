from __future__ import with_statement
import rpyc
import unittest
from dataclasses import dataclass


@dataclass
class StdTypes:
    exposed_intObj: int = 31
    exposed_strObj: str = "stdtypes string"
    exposed_floatObj: float = 3.14
    exposed_bytesObj: bytes = b"stdtypes bytes"


class MyService(rpyc.Service):

    def exposed_create_dataclass(self):
        return StdTypes()


class TestRemoteDataclass(unittest.TestCase):
    def setUp(self):
        self.server = rpyc.utils.server.OneShotServer(MyService, port=0)
        self.server.logger.quiet = False
        self.server._start_in_thread()
        self.conn = rpyc.connect("localhost", port=self.server.port)

    def tearDown(self):
        self.conn.close()

    def test_remote_dataclass(self):
        remote_dataclass = self.conn.root.create_dataclass()
        self.assertEqual(31, remote_dataclass.intObj())
        self.assertEqual("stdtypes string", remote_dataclass.strObj)
        self.assertEqual(3.14, remote_dataclass.floatObj)
        self.assertEqual(b"stdtypes bytes", remote_dataclass.bytesObj)


if __name__ == "__main__":
    unittest.main()
