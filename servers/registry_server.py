#!/usr/bin/env python
"""
The registry server listens to broadcasts on UDP port 18812, answering to
discovery queries by clients and registering keepalives from all running 
servers. In order for clients to use discovery, a registry service must
be running somewhere on their local network.
"""
from rpyc.utils.registry import RegistryServer


server = RegistryServer()
server.start()


