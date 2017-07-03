#!/usr/bin/env python
from __future__ import with_statement
import daemon
import lockfile
import sys
import signal
from rpyc.utils.server import ThreadedServer, ForkingServer
from rpyc.core.service import SlaveService
from rpyc.lib import setup_logger
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

server = None

def start():
    global server

    conf = ConfigParser()
    conf.read('rpycd.conf')

    mode = conf.get("rpycd", "mode").lower()
    if mode == "threaded":
        factory = ThreadedServer
    elif mode == "forking":
        factory = ForkingServer
    else:
        raise ValueError("Invalid mode %r" % (mode,))

    setup_logger(conf.getboolean("rpycd", "quiet"), conf.get("rpycd", "logfile"))

    server = factory(SlaveService, hostname = conf.get("rpycd", "host"),
        port = conf.getint("rpycd", "port"), reuse_addr = True)
    server.start()

def reload(*args):
    server.close()
    start()

def stop(*args):
    server.close()
    sys.exit()


if __name__ == "__main__":
    with daemon.DaemonContext(
            pidfile = lockfile.FileLock('/var/run/rpydc.pid'),
            signal_map = {signal.SIGTERM: stop, signal.SIGHUP: reload}):
        start()

