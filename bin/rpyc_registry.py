#!/usr/bin/env python
"""
The registry server listens to broadcasts on UDP port 18812, answering to
discovery queries by clients and registering keepalives from all running
servers. In order for clients to use discovery, a registry service must
be running somewhere on their local network.
"""
from plumbum import cli
from rpyc.utils.registry import REGISTRY_PORT, DEFAULT_PRUNING_TIMEOUT
from rpyc.utils.registry import UDPRegistryServer, TCPRegistryServer
from rpyc.lib import setup_logger


class RegistryServer(cli.Application):
    mode = cli.SwitchAttr(["-m", "--mode"], cli.Set("UDP", "TCP"), default = "UDP",
        help = "Serving mode")
    
    ipv6 = cli.Flag(["-6", "--ipv6"], help="use ipv6 instead of ipv4")

    port = cli.SwitchAttr(["-p", "--port"], cli.Range(0, 65535), default = REGISTRY_PORT, 
        help = "The UDP/TCP listener port")
    
    logfile = cli.SwitchAttr(["--logfile"], str, default = None, 
        help = "The log file to use; the default is stderr")
    
    quiet = cli.SwitchAttr(["-q", "--quiet"], help = "Quiet mode (only errors are logged)")
    
    pruning_timeout = cli.SwitchAttr(["-t", "--timeout"], int, 
        default = DEFAULT_PRUNING_TIMEOUT, help = "Set a custom pruning timeout (in seconds)")

    def main(self):
        if self.mode == "UDP":
            server = UDPRegistryServer(host = '::' if self.ipv6 else '0.0.0.0', port = self.port, 
                pruning_timeout = self.pruning_timeout)
        elif self.mode == "TCP":
            server = TCPRegistryServer(port = self.port, pruning_timeout = self.pruning_timeout)
        setup_logger(self.quiet, self.logfile)
        server.start()


if __name__ == "__main__":
    RegistryServer.run()

