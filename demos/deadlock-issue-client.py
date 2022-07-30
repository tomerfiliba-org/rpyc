import time
import rpyc

_dispatch = rpyc.core.protocol.Connection._dispatch

def _new_dispatch(self, data):
    time.sleep(0.0)
    return _dispatch(self, data)

setattr(rpyc.core.protocol.Connection, '_dispatch', _new_dispatch)
conn = rpyc.classic.connect("localhost")
bg_threads = []

for i in range(3):
    bg_threads.append(rpyc.BgServingThread(conn))

if __name__ == "__main__":
    t0 = time.time()
    conn.execute("import time")
    print(time.time() - t0)
    print(repr(conn._recvlock))
