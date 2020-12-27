#!/usr/bin/env python3
import time
import signal
import multiprocessing as mp
import pdb  # noqa
import rpyc
import traceback


def echo_once():
    start = time.time()
    conn = rpyc.connect("localhost", 18861, config={"sync_request_timeout": None})
    cdelta = time.time() - start
    addr, port = conn._channel.stream.sock.getsockname()
    fileno = conn.fileno()
    start = time.time()
    conn.root.echo("Echo")
    edelta = time.time() - start
    conn.close()
    return cdelta, edelta, fileno, addr, port


def echo_forever(main_event):
    try:
        count = 0
        edelta = 0
        cdelta = 0
        _max = {'edelta': 0, 'cdelta': 0}
        fileno = "unknown"
        addr = "unknown"
        port = "unknown"
        cdelta = -1
        edelta = -1
        while main_event.is_set():
            count += 1
            cdelta, edelta, fileno, addr, port = echo_once()
            _max['cdelta'] = cdelta
            _max['edelta'] = edelta
    except KeyboardInterrupt:
        if main_event.is_set():
            main_event.clear()
    except Exception:
        tb = f"EXCEPT ('{addr}', {port}) with fd {fileno} over cdelta {cdelta} and delta {edelta}\n"
        tb += traceback.format_exc()

        return None, tb
    finally:
        return _max, None


def echo_client_pool(client_limit):
    try:
        sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = mp.Pool(processes=client_limit)
        signal.signal(signal.SIGINT, sigint)
        eid_proc = {}
        pool_manager = mp.Manager()
        main_event = pool_manager.Event()
        main_event.set()
        for eid in range(client_limit):
            eid_proc[eid] = pool.apply_async(func=echo_forever, args=(main_event,))
        while True:
            alive = len([r for r in eid_proc.values() if not r.ready()])
            print('{0}/{1} alive'.format(alive, client_limit))
            if alive == 1:
                print('All of the client processes are dead except one. Exiting loop...')
                break
            else:
                time.sleep(1)
        res = [r.get() for r in eid_proc.values() if r.ready()]
        cdelta = [_max['cdelta'] for _max, tb in res if _max]
        edelta = [_max['edelta'] for _max, tb in res if _max]
        if cdelta:
            cdelta = max(cdelta)
        else:
            cdelta = "unknown"
        if edelta:
            edelta = max(edelta)
        else:
            edelta = "unknown"
        time.sleep(1)
        print(f"Max time to establish: {cdelta}")
        print(f"Max time   echo reply: {edelta}")
        main_event.clear()
    except KeyboardInterrupt:
        main_event.clear()
        for proc in eid_proc.values():
            proc.terminate()


def main(client_limit):
    if client_limit == 1:
        echo_once()
    else:
        echo_client_pool(client_limit)


if __name__ == "__main__":
    main(client_limit=5)
