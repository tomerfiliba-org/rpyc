from rpyc.lib.compat import BYTES_LITERAL
from rpyc.core.stream import PipeStream, NamedPipeStream
import rpyc
import sys
import time
import unittest


@unittest.skipIf(sys.platform != "win32", "Requires windows")
class Test_Pipes(unittest.TestCase):
    def test_basic_io(self):
        p1, p2 = PipeStream.create_pair()
        p1.write(BYTES_LITERAL("hello"))
        assert p2.poll(0)
        assert p2.read(5) == BYTES_LITERAL("hello")
        assert not p2.poll(0)
        p2.write(BYTES_LITERAL("world"))
        assert p1.poll(0)
        assert p1.read(5) == BYTES_LITERAL("world")
        assert not p1.poll(0)
        p1.close()
        p2.close()

    def test_rpyc(self):
        p1, p2 = PipeStream.create_pair()
        client = rpyc.connect_stream(p1)
        server = rpyc.connect_stream(p2)
        server_thread = rpyc.spawn(server.serve_all)
        assert client.root.get_service_name() == "VOID"
        t = rpyc.BgServingThread(client)
        assert server.root.get_service_name() == "VOID"
        t.stop()
        client.close()
        server.close()
        server_thread.join()


@unittest.skipIf(sys.platform != "win32", "Requires windows")
class Test_NamedPipe(object):
    def setUp(self):
        self.pipe_server_thread = rpyc.spawn(self.pipe_server)
        time.sleep(1)  # make sure server is accepting already
        self.np_client = NamedPipeStream.create_client("floop")
        self.client = rpyc.connect_stream(self.np_client)

    def tearDown(self):
        self.client.close()
        self.server.close()
        self.pipe_server_thread.join()

    def pipe_server(self):
        self.np_server = NamedPipeStream.create_server("floop")
        self.server = rpyc.connect_stream(self.np_server)
        self.server.serve_all()

    def test_rpyc(self):
        assert self.client.root.get_service_name() == "VOID"
        t = rpyc.BgServingThread(self.client)
        assert self.server.root.get_service_name() == "VOID"
        t.stop()


if __name__ == "__main__":
    unittest.main()
