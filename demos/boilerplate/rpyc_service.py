import rpyc
import os
from threading import Thread
import time


class MyServiceFactory(rpyc.Service):

    class exposed_MyService(object):   # exposing names is not limited to methods :)

        def __init__(self, filename, callback, interval = 1):
            print("news client with " + filename + " " + str(callback))
            self.filename = filename
            self.interval = interval
            self.last_stat = None
            self.callback = rpyc.async_(callback)   # create an async callback
            self.active = True
            self.thread = Thread(target = self.work)
            self.thread.start()

        def exposed_stop(self):   # this method has to be exposed too
            self.active = False
            self.thread.join()

        def work(self):
            while self.active:
                stat = os.stat(self.filename)
                if self.last_stat is not None and self.last_stat != stat:
                    self.callback(self.last_stat, stat)   # notify the client of the change
                self.last_stat = stat
                time.sleep(self.interval)
            print("client closed.")
