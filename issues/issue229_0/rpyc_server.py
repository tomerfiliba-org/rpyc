import logging
import itertools

import rpyc
from rpyc.utils.server import OneShotServer

ping_counter = itertools.count()

class PingService(rpyc.Service):

    def exposed_ping(self):
        count = next(ping_counter)
        print("ping received: {}".format(count))
        return count

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    s = OneShotServer(PingService, port=18861)
    s.start()
