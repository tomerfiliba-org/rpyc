#!/usr/bin/env python3
import logging
import functools
import rpyc
import threading
import random
import time


THREAD_SAFE = True  # Toggles thread safe and unsafe behavior


def synchronize(lock):
    """ Decorator that invokes the lock acquire call before a function call and releases after """
    def sync_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock.acquire()
            res = func(*args, **kwargs)
            lock.release()
            return res
        return wrapper
    return sync_func


class SharingComponent(object):
    """ Initialized in the class definition of SharingService and shared by all instances of SharingService """
    lock = threading.Lock()

    def __init__(self):
        self.sequence_id = 0

    def sleepy_sequence_id(self):
        """ increment id and sometimes sleep to force race condition """
        self.sequence_id += 1
        _expected_sequence_id = self.sequence_id
        if random.randint(0, 1) == 1:
            time.sleep(1)
        if self.sequence_id == _expected_sequence_id:
            return self.sequence_id
        else:
            raise RuntimeError("Unexpected sequence_id behavior (race condition).")

    @synchronize(lock)
    def get_sequence_id(self):
        """ provides a thread-safe execution frame to otherwise unsafe functions """
        return self.sleepy_sequence_id()


class SharingService(rpyc.Service):
    """ A class that allows for sharing components between connection instances """
    __shared__ = SharingComponent()

    @property
    def shared(self):
        """ convenient access to an otherwise long object name """
        return SharingService.__shared__

    def exposed_echo(self, message):
        """ example of the potential perils when threading shared state """
        if THREAD_SAFE:
            seq_id = self.shared.get_sequence_id()
        else:
            seq_id = self.shared.sleepy_sequence_id()
        if message == "Echo":
            return f"Echo Reply {seq_id}"
        else:
            return f"Parameter Problem {seq_id}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    debugging_config = {'allow_all_attrs': True, 'sync_request_timeout': None}
    echo_svc = rpyc.ThreadedServer(service=SharingService, port=18861, protocol_config=debugging_config)
    echo_svc.start()
