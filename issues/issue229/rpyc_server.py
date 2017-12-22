import socket
import logging
import itertools

from connection import Service, SocketStream, Channel, Connection

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("localhost", 18861))
    listener.listen(1)
    logger.info("server started %s", listener.getsockname())

    sock, addrinfo = listener.accept()
    sock.setblocking(True)

    logger.info("welcome %s", addrinfo)
    config = dict({}, credentials = None,
        endpoints = (sock.getsockname(), addrinfo), logger=logger)
    conn = Connection(Service, Channel(SocketStream(sock)),
        config = config, _lazy = True)
    while True:
        conn.serve(None)
