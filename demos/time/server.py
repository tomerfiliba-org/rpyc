from rpyc.utils.server import ThreadedServer
from time_service import TimeService


if __name__ == "__main__":
    s = ThreadedServer(TimeService)
    s.start()

