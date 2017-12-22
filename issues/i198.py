#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys
import rpyc
from rpyc.utils.server import ThreadedServer


class XmppService(rpyc.Service):
    def on_connect(self):
        # code that runs when a connection is created
        # (to init the serivce, if needed)
        pass

    def on_disconnect(self):
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_send_mensage(self, msg, to=None):
        print("Accessed bot: {}".format(self.exposed_bot))

    def exposed_login(self):
        self.exposed_bot = 42
        print("Created bot: {}".format(self.exposed_bot))

if __name__ == "__main__":
    if len(sys.argv)>1:
        if sys.argv[1]=="login":
            c = rpyc.connect("localhost", 18861)
            c.root.login()
        else:
            c = rpyc.connect("localhost", 18861)
            c.root.send_mensage(" ".join(sys.argv[1:]))
    else:
        t = ThreadedServer(XmppService, port = 18861)
        t.start()
