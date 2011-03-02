import platform
from rpyc.core.stream import SocketStream, PipeStream
from rpyc.core.channel import Channel
from rpyc.core.protocol import Connection
from rpyc.core.netref import BaseNetref
from rpyc.core.async import AsyncResult, AsyncResultTimeout
from rpyc.core.service import Service, VoidService, SlaveService
from rpyc.core.vinegar import GenericException, install_rpyc_excepthook

# on .NET
if platform.system() == 'cli':
    import clr
    # Add Reference to IronPython zlib (required for channel compression) 
    # grab it from http://bitbucket.org/jdhardy/ironpythonzlib
    clr.AddReference("IronPython.Zlib") 

install_rpyc_excepthook()

