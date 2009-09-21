import rpyc
import os
import time
from threading import Thread

class FileMonitorService(rpyc.Service):
    class exposed_FileMonitor(object):
        def __init__(self, filename, callback, interval = 1):
            self.filename = filename
            self.interval = interval
            self.last_stat = None
            self.callback = rpyc.async(callback)   # make the callback async
            self.active = True
            self.thread = Thread(target = self.work)
            self.thread.start()
        def exposed_stop(self):
            self.active = False
            self.thread.join()
        def work(self):
            while self.active:
                stat = os.stat(self.filename)
                if self.last_stat is not None and self.last_stat != stat:
                    self.callback(self.last_stat, stat)
                self.last_stat = stat
                time.sleep(self.interval)


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    ThreadedServer(FileMonitorService, port = 18871).start()

