import time
from rpyc import Service


class TimeService(Service):
    def exposed_get_utc(self):
        return time.time()

    def exposed_get_time(self):
        return time.ctime()

