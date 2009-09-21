#!/usr/bin/env python
import rpyc
from rpyc.utils.twisted_integration import RpycServerFactory
from twisted.internet import reactor


class MyService(rpyc.Service):
    def exposed_add(self, a, b):
        return a + b
    def exposed_call(self, func):
        rpyc.async(func)(18)
    def exposed_quit(self):
        reactor.callLater(0, reactor.stop)

#reactor.listenTCP(18812, RpycServerFactory(rpyc.SlaveService))
#reactor.listenTCP(18814, RpycServerFactory(MyService, logging = True))

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1])
    reactor.listenTCP(port, RpycServerFactory(MyService, logging = True))
    print "started listening on %s" % (port,)
    reactor.run()



