#!/usr/bin/env python
"""Shows expected behavior for a client when the remote thread serving this client is busy/sleeping.

Additional context: https://github.com/tomerfiliba-org/rpyc/issues/491#issuecomment-1131843406
"""
import rpyc
import threading
import time


def async_example(connection):
    t0 = time.time()
    print(f"Running async example...")
    _async_function = rpyc.async_(connection.root.function)
    res = _async_function(threading.Event())
    print(f"Created async result after {time.time()-t0}s")
    value = res.value
    print(f"Value returned after {time.time()-t0}s: {value}")
    print()


def synchronous_example(connection):
    t0 = time.time()
    print(f"Running synchronous example...")
    value = connection.root.function(threading.Event())
    print(f"Value returned after {time.time()-t0}s: {value}")
    print()


if __name__ == "__main__":
    connection = rpyc.connect("localhost", 18812, config=dict(allow_public_attrs=True))
    async_example(connection)
    synchronous_example(connection)
