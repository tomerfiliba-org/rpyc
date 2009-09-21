"""
RPyC -- Remote Python Call
http://rpyc.sourceforge.net
by Tomer Filiba (tomerfiliba at gmail dot com)
"""
import sys
from Lib import rpyc_excepthook
from Utils import *


#
# API
#
__all__ = [
    # Factories
    "SocketConnection", "PipeConnection", "SecSocketConnection", "Async",
    # Builtins
    "dir", "getattr", "hasattr", "reload", "help", "isinstance", "issubclass",
    # Helpers
    "obtain", "deliver", "isproxy", "getconn",
    # Files
    "upload", "download",
    # Discovery
    "discover_servers",
]

__version__ = (2, 60)


#
# install custom exception hook
#
sys.excepthook = rpyc_excepthook
