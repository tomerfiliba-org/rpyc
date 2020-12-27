#!/usr/bin/env python3
import inspect
import logging
# import gevent
# from gevent import monkey
# monkey.patch_all()
import rpyc


class EchoService(rpyc.Service):
    def on_connect(self, conn):
        msg = f"on connect service peer name: {conn._channel.stream.sock.getpeername()}"
        conn._config["logger"].debug(msg)

    def on_disconnect(self, conn):
        pass

    def exposed_echo(self, message):
        if message == "Echo":
            return "Echo Reply"
        else:
            return "Parameter Problem"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    echo_svc = rpyc.OneShotServer(service=EchoService, port=18861, protocol_config={'allow_all_attrs': True})
    echo_svc.start()
