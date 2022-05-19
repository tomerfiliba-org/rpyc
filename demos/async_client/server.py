#!/usr/bin/env python
"""Emulates a service function that is blocked due to being busy/sleeping.

Additional context: https://github.com/tomerfiliba-org/rpyc/issues/491#issuecomment-1131843406
"""
import rpyc
import threading
import time


class Service(rpyc.Service):
    def exposed_function(self, event):
        threading.Thread(target=event.wait).start()
        time.sleep(1)
        threading.Thread(target=event.set).start()
        return 'silly sleeps on server threads'


if __name__ == "__main__":
    rpyc.ThreadedServer(Service(), hostname="localhost", port=18812).start()
