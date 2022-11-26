#!/usr/bin/env python
"""Emulates a service function that is blocked due to being busy/sleeping.

Additional context: https://github.com/tomerfiliba-org/rpyc/issues/491#issuecomment-1131843406
"""
import logging
import time
import rpyc
import threading


logger = rpyc.setup_logger(namespace='server')
rpyc.core.protocol.DEFAULT_CONFIG['logger'] = logger


class Service(rpyc.Service):
    def exposed_fetch_value(self):
        return self._value

    def exposed_function(self, client_event, block_server_thread=False):
        if block_server_thread:
            # For some reason
            def _wait(): return getattr(client_event, 'wait')()  # delays attr proxy behavior
            def _set(): return getattr(client_event, 'set')()  # delays attr proxy behavior
        else:
            _wait = rpyc.async_(client_event.wait)  # amortize proxy behavior
            _set = rpyc.async_(client_event.set)  # amortize proxy behavior
        _wait()
        logger.debug('Client messaged to wait for now...')
        for i in (1, 2):
            logger.debug(f'Pretending to do task {i}')
            time.sleep(0.2)
        self._value = 6465616462656566  # ''.join([hex(ord(c))[2:] for c in 'deadbeef'])
        _set()
        logger.debug('Client event set, it may resume...')


if __name__ == "__main__":
    rpyc.ThreadedServer(service=Service, hostname="localhost", port=18812).start()
