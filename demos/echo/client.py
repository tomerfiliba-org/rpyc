#!/usr/bin/env python3
import time
import pdb  # noqa
import rpyc


if __name__ == "__main__":
    count = 0
    while True:
        conn = rpyc.connect("localhost", 18861)
        count += 1
        start = time.time()
        reply = conn.root.echo("Echo")
        delta = time.time() - start
        print("{} #{} took: {}s".format(reply, count, delta))
        conn.close()
