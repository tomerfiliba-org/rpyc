import rpyc.lib
from rpyc.utils.server import ThreadedServer

rpyc_protocol_config = {
    'allow_all_attrs': True,
    'allow_public_attrs': True,
    'allow_exposed_attrs': True,
    'exposed_prefix': '',
}

class TouchstoneRemoteService(rpyc.Service):

    foo = "bar"

rpyc.lib.setup_logger()

t = ThreadedServer(TouchstoneRemoteService,
                   port = 18861,
                   protocol_config=rpyc_protocol_config)
t.start()
