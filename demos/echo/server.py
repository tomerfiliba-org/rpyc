#!/usr/bin/env python3
import inspect
import logging
import gevent
from gevent import monkey
monkey.patch_all()
import rpyc
from rpyc.utils.server import OneShotServer, ThreadedServer


class EchoService(rpyc.Service):
    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass

    def exposed_echo(self, message):
        if message == "Echo":
            return "Echo Reply"
        else:
            return "Parameter Problem"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    choice = 'ForkingServer' # Leak
    svc_server = None
    server_class = {}
    # Populate for 'ForkingServer', 'GeventServer', 'OneShotServer', 'ThreadPoolServer', and 'ThreadedServer'
    for name, value in inspect.getmembers(rpyc.utils.server, inspect.isclass):
        if rpyc.utils.server.Server in getattr(value, '__mro__', []):
            server_class[name] = value
    svc_server = server_class[choice]
    echo_svc = svc_server(service=EchoService, port=18861, protocol_config={'allow_all_attrs': True})
    echo_svc.start()
