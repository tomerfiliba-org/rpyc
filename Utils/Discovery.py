"""
Discovery: broadcasts a query, attempting to discover all running RPyC servers
over the local network/specific subnet.
"""
import socket
import select
import struct


__all__ = ["discover_servers"]
UDP_DISCOVERY_PORT = 18813
QUERY_MAGIC = "RPYC_QUERY"
MAX_DGRAM_SIZE = 100


def discover_servers(subnet = "255.255.255.255", timeout = 1):
    """broadcasts a query and returns a list of (addr, port) of running servers"""
    # broadcast
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(QUERY_MAGIC, (subnet, UDP_DISCOVERY_PORT))
    
    # wait for replies
    replies = []
    while True:
        rlist, dummy, dummy = select.select([s], [], [], timeout)
        if not rlist:
            break
        data, (addr, port) = s.recvfrom(MAX_DGRAM_SIZE)
        rpyc_port, = struct.unpack("<H", data)
        replies.append((addr, rpyc_port))

    return list(set(replies))





