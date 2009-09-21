#!/usr/bin/env python
# 
# installation instructions
#  * add a service in /etc/services for rpyc: tcp port 18812
#  * add "rpyc .... /usr/lib/pythonXX/site-packages/Rpyc/Servers/std_server.py"
#    to /etc/inetd.conf (i dont remember syntax, rtfm)
#  * dont forget to chmod +x this file
#  * restart inetd with sighup
#
import sys
import time
from traceback import format_exception
from Rpyc.Utils.Serving import log, serve_pipes


def main(filename = "/tmp/rpyc-server.log"):
    log.logfile = open(filename, "a")
    log("-" * 80)
    log("started serving at", time.asctime())
    try:
        try:
            serve_pipes(sys.stdin, sys.stdout)
        except:
            log(*format_exception(*sys.exc_info()))
    finally:
        log("server exits at", time.asctime())

if __name__ == "__main__":
    main()
    
    