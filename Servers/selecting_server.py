import select
import socket
from Rpyc.Utils.Serving import (
    log, 
    create_listener_socket, 
    DEFAULT_PORT, 
    SocketStream, 
    Channel,
    Connection)


def main(port = DEFAULT_PORT):
    sock = create_listener_socket(port)
    connections = []
    
    while True:
        rlist, wlist, xlist = select.select([sock] + connections, [], [])
        
        if sock in rlist:
            rlist.remove(sock)
            newsock, name = sock.accept()
            conn = Connection(Channel(SocketStream(newsock)))
            conn.sockname = name
            connections.append(conn)
            log("welcome", conn.sockname)
        
        for conn in rlist:
            try:
                conn.serve()
            except (EOFError, socket.error):
                connections.remove(conn)
                log("goodbyte", conn.sockname)

if __name__ == "__main__":
    main()
