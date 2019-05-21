#!/usr/bin/env python3
import time
import signal
import os, sys
from multiprocessing import Pool, Event
import pdb  # noqa
import rpyc


def echo_forever(evnt):
    # sys.stdout = open(os.devnull, 'w')
    try:
        count = 0
        while evnt.is_set():
            conn = rpyc.connect("localhost", 18861)
            count += 1
            start = time.time()
            reply = conn.root.echo("Echo")
            delta = time.time() - start
            conn.close()
            # print("{} #{} took: {}s".format(reply, count, delta))
    except KeyboardInterrupt:
        os._exit(1)


def main():
    try:
        limit = 256
        sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = Pool(processes=limit)              # start 4 worker processes
        signal.signal(signal.SIGINT, sigint)
        main_evnt = Event()
        main_evnt.set()
        eid_proc = {}
        for eid in range(limit):
            proc = pool.Process(target=echo_forever, args=(main_evnt,))
            proc.daemon = True
            proc.start()
            eid_proc[eid] = proc
        while True:
            alive = len([proc for proc in eid_proc.values() if proc.is_alive()])
            print('{}/{} alive'.format(alive, limit))
            time.sleep(1)
    except KeyboardInterrupt:
        main_evnt.clear()
        for proc in eid_proc.values():
            proc.join()
        os._exit(0)



if __name__ == "__main__":
    main()
