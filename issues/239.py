import unittest
from rpyc.utils.server import ThreadedServer
import rpyc
import threading

class TestService(rpyc.Service):
    def _rpyc_getattr(self, name):
        raise AttributeError()

    def __call__(self):
        print("OH NO")
       
    def hidden(self):
        print("Can't get here")

def test_simple_client_server(): #tests family_exclude and preference order too
        port=18861

        #THIS SHOULD BLOCK EVERYTHING NOT EXPOSED BY _rpyc_getattr
        config={ "allow_safe_attrs":False,
                 "allow_exposed_attrs":False,
                 "allow_getattr":False }

        server=ThreadedServer( TestService, hostname="localhost", port=port, protocol_config=config )
        serverThread = threading.Thread( target=server.start, args=())        
        serverThread.start()

        connection=rpyc.connect("localhost" , port)

        root=connection.root

        root.__call__() #This should not work
        root() #in an ideal world this shouldn't work either.

        connection.close()

        server.close()
        serverThread.join()

if __name__=="__main__":
    test_simple_client_server()
