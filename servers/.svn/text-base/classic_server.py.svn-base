#!/usr/bin/env python
"""
classic rpyc server (threaded, forking or std) running a SlaveService
usage: 
    classic_server.py                         # default settings
    classic_server.py -m forking -p 12345     # custom settings
"""
import sys
import os
import rpyc
from optparse import OptionParser
from rpyc.utils.server import ThreadedServer, ForkingServer, DEFAULT_SERVER_PORT
from rpyc.core import SlaveService


parser = OptionParser()
parser.add_option("-m", "--mode", action="store", dest="mode", metavar="MODE",
    default="threaded", type="string", help="mode can be 'threaded', 'forking', "
    "or 'stdio' to operate over the standard IO pipes (for inetd, etc.)")
parser.add_option("-p", "--port", action="store", dest="port", type="int", 
    metavar="PORT", default=DEFAULT_SERVER_PORT, help="specify a different TCP listener port")
parser.add_option("-f", "--file", action="store", dest="logfile", type="str", 
    metavar="FILE", default=None, help="specify the log file to use; the default is stderr")
parser.add_option("-q", "--quiet", action="store_true", dest="quiet", 
    default=False, help="quiet mode (no logging). in stdio mode, writes to /dev/null")

options, args = parser.parse_args()
if args:
    raise ValueError("does not take positional arguments: %r" % (args,))

options.mode = options.mode.lower()
if options.mode == "threaded":
    t = ThreadedServer(SlaveService, port = options.port, reuse_addr = True)
    t.logger.quiet = options.quiet
    if options.logfile:
        t.logger.console = open(options.logfile)
    t.start()
elif options.mode == "forking":
    t = ForkingServer(SlaveService, port = options.port, reuse_addr = True)
    t.logger.quiet = options.quiet
    if options.logfile:
        t.logger.console = open(options.logfile)
    t.start()
elif options.mode == "stdio":
    origstdin = sys.stdin
    origstdout = sys.stdout
    if options.quiet:
        dev = os.devnull
    elif sys.platform == "win32":
        dev = "con:"
    else:
        dev = "/dev/tty"
    try:
        sys.stdin = open(dev, "r")
        sys.stdout = open(dev, "w")
    except (IOError, OSError):
        sys.stdin = open(os.devnull, "r")
        sys.stdout = open(os.devnull, "w")
    conn = rpyc.classic.connect_pipes(origstdin, origstdout)
    try:
        try:
            conn.serve_all()
        except KeyboardInterrupt:
            print "User interrupt!"
    finally:
        conn.close()
else:
    raise ValueError("invalid mode %r" % (options.mode,))

