"""
.
         #####    #####             ####
        ##   ##  ##   ##           ##             ####      
        ##  ##   ##  ##           ##                 #
        #####    #####   ##   ##  ##               ## 
        ##  ##   ##       ## ##   ##                 #
        ##   ##  ##        ###    ##              ###
        ##   ##  ##        ##      #####         
     -------------------- ## ------------------------------------------
                         ##

Remote Python Call (RPyC) v $$VERSION$$, $$DATE$$
Licensed under the MIT license (see `LICENSE` file)

A transparent, symmetric and light-weight RPC and distributed computing 
library for python.

Usage:
    import rpyc
    c = rpyc.connect_by_service("SERVICENAME")
    print c.root.some_function(1, 2, 3)

Classic-style usage:
    import rpyc
    # `hostname` is assumed to be running a slave-service server
    c = rpyc.classic.connect("hostname") 
    print c.execute("x = 5")
    print c.eval("x + 2")
    print c.modules.os.listdir(".")
    print c.modules["xml.dom.minidom"].parseString("<a/>")
    f = c.builtin.open("foobar.txt", "rb")
    print f.read(100)
"""
from rpyc.core import (SocketStream, TunneledSocketStream, PipeStream, Channel, 
    Connection, Service, BaseNetref, AsyncResult, GenericException, 
    AsyncResultTimeout, VoidService, SlaveService)
from rpyc.utils.factory import (connect_stream, connect_channel, connect_pipes, 
    connect_stdpipes, connect, tlslite_connect, ssl_connect, discover, 
    connect_by_service, connect_subproc, connect_thread)
from rpyc.utils.helpers import async, timed, buffiter, BgServingThread
from rpyc.utils import classic
from rpyc.version import version, version_string, release_date

__author__ = "Tomer Filiba (tomerfiliba@gmail.com)"
__version__ = version
__doc__ = __doc__.replace("$$VERSION$$", version_string).replace("$$DATE$$", release_date)
del version_string, release_date

