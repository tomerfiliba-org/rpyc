import sys
import time
import rpyc
from testbase import TestBase
from rpyc.core.stream import PipeStream, NamedPipeStream
from threading import Thread


class PipeTest(TestBase):
    def setup(self):
        if sys.platform != "win32":
            self.cannot_run("this test requires win32")
    
    def step_basic_io(self):
        p1, p2 = PipeStream.create_pair()
        p1.write("hello")
        self.require(p2.poll(0))
        self.require(p2.read(5) == "hello")
        self.require(not p2.poll(0))
        p2.write("world")
        self.require(p1.poll(0))
        self.require(p1.read(5) == "world")
        self.require(not p1.poll(0))
        p1.close()
        p2.close()
    
    def step_rpyc(self):
        p1, p2 = PipeStream.create_pair()
        client = rpyc.connect_stream(p1)
        server = rpyc.connect_stream(p2)
        server_thread = Thread(target = server.serve_all)
        server_thread.start()
        self.require(client.root.get_service_name() == "VOID")
        t = rpyc.BgServingThread(client)
        self.require(server.root.get_service_name() == "VOID")
        t.stop()
        client.close()
        server.close()
        server_thread.join()


class NamedPipeTest(TestBase):
    def setup(self):
        if sys.platform != "win32":
            self.cannot_run("this test requires win32")
        
        self.pipe_server_thread = Thread(target = self.pipe_server)
        self.pipe_server_thread.start()
        time.sleep(1) # make sure server is accepting already
        self.np_client = NamedPipeStream.create_client("floop")
        self.client = rpyc.connect_stream(self.np_client)
    
    def cleanup(self):
        self.client.close()
        self.server.close()
        self.pipe_server_thread.join()
    
    def pipe_server(self):
        self.np_server = NamedPipeStream.create_server("floop")
        self.server = rpyc.connect_stream(self.np_server)
        self.server.serve_all()
    
    def step_rpyc(self):
        self.require(self.client.root.get_service_name() == "VOID")
        t = rpyc.BgServingThread(self.client)
        self.require(self.server.root.get_service_name() == "VOID")
        t.stop()


if __name__ == "__main__":
    PipeTest.run()
    NamedPipeTest.run()






