from rpyc.utils.server import ThreadedServer
from rpyc_service import MyServiceFactory

if __name__ == "__main__":
    ThreadedServer(MyServiceFactory, port = 18000).start()