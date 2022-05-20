#!/usr/bin/env python
"""Shows expected behavior for a client when the remote thread serving this client is busy/sleeping.

Additional context: https://github.com/tomerfiliba-org/rpyc/issues/491#issuecomment-1131843406
"""
import logging
import threading
import time
import rpyc


logger = rpyc.setup_logger(namespace='client')
rpyc.core.protocol.DEFAULT_CONFIG['logger'] = logger


def async_example(connection, event):
    _async_function = rpyc.async_(connection.root.function)  # create async proxy
    # The server will call event.wait which will block this thread. To process
    # the set message from the server we need a background thread. A background
    # thread ensures that we have a thread that is not blocked.
    #
    # But wait! Since the communication is symmetric, the server side could
    # be blocked if you are not careful. It needs responses from the client
    #
    # The perils of trying to thread a single connection...
    # - the thread the receives the message from the server to wait is blocked
    # - which thread is blocked is VERY hard to guarantee
    #
    # THIS IS NOT HE PREFERRED WAY FOR MUTABLE TYPES...
    # - threading a connection might be okay to do for immutable types depending on context

    bgsrv = rpyc.BgServingThread(connection)
    ares = _async_function(event, block_server_thread=False)
    value = ares.value
    event.clear()
    logger.info('Running buggy blocking example...')
    ares = _async_function(event, block_server_thread=True)
    value = ares.value
    event.clear()
    bgsrv.stop()


def how_to_block_main_thread(connection, event):
    """Example of how to block the main thread of a client"""
    t0 = time.time()
    logger.debug("Running example that blocks main thread of client...")
    value = connection.root.function(event, call_set=True)
    logger.debug(f"Value returned after {time.time()-t0}s: {value}")


class Event:
    def __init__(self):
        self._evnt = threading.Event()

    def __getattr__(self, name):
        if name in ('wait', 'set', 'clear'):
            logging.info(f'Event.__getattr__({name})')
        return getattr(self._evnt, name)


if __name__ == "__main__":
    logger.info('Printed from main thread')
    connection = rpyc.connect("localhost", 18812, config=dict(allow_all_attrs=True))
    event = Event()
    async_example(connection, event)
    event.clear()
    # how_to_block_main_thread_example(connection, event)
