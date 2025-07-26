import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import unittest
try:
    import urllib3
    urllib3.request
    _urllib3_import_failed = False
except Exception:
    _urllib3_import_failed = True


@unittest.skipIf(_urllib3_import_failed or True, "urllib3 not available")
class TestUrllib3(unittest.TestCase):
    """ #547 """

    def setUp(self):
        self.cfg = {'sync_request_timeout': 60*60}
        self.server = ThreadedServer(SlaveService, port=18878, auto_register=False, protocol_config=self.cfg)
        self.server.logger.quiet = False
        self.thd = self.server._start_in_thread()
        self.conn = rpyc.classic.connect('localhost', port=18878)

    def tearDown(self):
        self.conn.close()
        self.server.close()
        self.thd.join()

    def test_issue(self):
        self.conn.execute('import urllib3')
        urllib3_ = self.conn.modules.urllib3
        # headers = urllib3.HTTPHeaderDict()
        # headers.add("Accept", "application/json")
        # headers.add("Accept", "text/plain")
        headers = {"X-Request-Id": "test"}
        resp = urllib3_.request("POST", "https://httpbin.org/post", fields={"hello": "world"}, headers=headers)
        __import__('code').interact(local=locals() | globals())
        # self.assertTrue(self.conn.root.instance(remote_list, list))


if __name__ == "__main__":
    unittest.main()
