import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import unittest


class Test_get_id_pack(unittest.TestCase):

    def setUp(self):
        self.port = 18878
        self.port2 = 18879
        self.server = ThreadedServer(SlaveService, port=self.port, auto_register=False)
        self.server2 = ThreadedServer(SlaveService, port=self.port2, auto_register=False)
        self.server._start_in_thread()
        self.server2._start_in_thread()
        self.conn = rpyc.classic.connect("localhost", port=self.port)
        self.conn_rpyc = self.conn.root.getmodule('rpyc')
        self.chained_conn = self.conn_rpyc.connect('localhost', self.port2)

    def tearDown(self):
        self.chained_conn.close()
        self.conn.close()
        self.server.close()
        self.server2.close()

    def test_netref(self):
        self.assertEquals(self.conn.root.____id_pack__, rpyc.lib.get_id_pack(self.conn.root))

    def test_chained_connect(self):
        self.chained_conn.root.getmodule('os')

    def test_class_instance_wo_name(self):
        ss = rpyc.SlaveService()
        id_pack = rpyc.lib.get_id_pack(ss)
        self.assertEqual('rpyc.core.service.SlaveService', id_pack[0])

    def test_class_wo_name(self):
        ss = rpyc.SlaveService
        id_pack = rpyc.lib.get_id_pack(ss)
        self.assertEqual('rpyc.core.service.SlaveService', id_pack[0])


if __name__ == "__main__":
    unittest.main()
