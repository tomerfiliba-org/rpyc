#!/usr/bin/env python3
import time
import signal
from multiprocessing import Pool, Queue, Event
import pdb  # noqa
import rpyc


def echo_forever(main_queue, main_event):
    # sys.stdout = open(os.devnull, 'w')
    try:
        count = 0
        start = time.time()
        delta = 0
        cdelta = 0
        _max = {'delta': 0, 'cdelta': 0}
        fileno = "unknown"
        addr, port = "unknown", "unknown"
        while main_event.is_set():
            count += 1
            start = time.time()
            conn = rpyc.connect("localhost", 18861, config={"sync_request_timeout": 30})
            cdelta = time.time() - start
            addr, port = conn._channel.stream.sock.getsockname()
            fileno = conn.fileno()
            start = time.time()
            conn.root.echo("Echo")
            delta = time.time() - start
            conn.close()
            _max['delta'] = delta
            _max['cdelta'] = cdelta
    except KeyboardInterrupt:
        if main_event.is_set():
            main_event.clear()
    except Exception:
        import traceback
        traceback.print_exc()
        print("EXCEPT ('{}', {}) with fd {} over {}s".format(addr, port, fileno, cdelta + delta))
    finally:
        main_queue.put(_max)


def main():
    try:
        limit = 256
        sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = Pool(processes=limit)
        signal.signal(signal.SIGINT, sigint)
        eid_proc = {}
        main_queue = Queue()
        main_event = Event()
        main_event.set()
        for eid in range(limit):
            proc = pool.Process(target=echo_forever, args=(main_queue, main_event))
            proc.daemon = True
            proc.start()
            eid_proc[eid] = proc
        while True:
            alive = len([_proc for _proc in eid_proc.values() if _proc.is_alive()])
            print('{}/{} alive'.format(alive, limit))
            time.sleep(1)
    except (KeyboardInterrupt, Exception):
        main_event.clear()
        for proc in eid_proc.values():
            proc.terminate()
    finally:
        res = []
        while not main_queue.empty():
            res.append(main_queue.get())
        cdelta = [_max['cdelta'] for _max in res]
        delta = [_max['delta'] for _max in res]
        if cdelta:
            cdelta = max(cdelta)
        else:
            cdelta = "unknown"
        if delta:
            delta = max(delta)
        else:
            delta = "unknown"
        time.sleep(1)
        print("Max time to establish: {}".format(cdelta))
        print("Max time   echo reply: {}".format(delta))
        print(cdelta, delta)


if __name__ == "__main__":
    main()
