import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import unittest


class Test_get_id_pack(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.port = 18878
        cls.port2 = 18879
        cls.server = ThreadedServer(SlaveService, port=cls.port, auto_register=False)
        cls.server2 = ThreadedServer(SlaveService, port=cls.port2, auto_register=False)
        cls.thd = cls.server._start_in_thread()
        cls.thd2 = cls.server2._start_in_thread()
        cls.conn = rpyc.classic.connect("localhost", port=cls.port)
        cls.conn_rpyc = cls.conn.root.getmodule('rpyc')
        cls.chained_conn = cls.conn_rpyc.connect('localhost', cls.port2)

    @classmethod
    def tearDownClass(cls):
        cls.chained_conn.close()
        cls.conn.close()
        while cls.server2.clients or cls.server.clients:
            pass  #sti
        cls.server2.close()
        cls.server.close()
        cls.thd.join()
        cls.thd2.join()

    def test_chained_connect(self):
        remote_os = self.chained_conn.root.getmodule('os')

    def test_netref(self):
        self.assertEqual(self.conn.root.____id_pack__, rpyc.lib.get_id_pack(self.conn.root))

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
