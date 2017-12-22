import threading
import rpyc
import rpyc.utils.helpers
import rpyc.lib
import time


rpyc.lib.setup_logger()
conn = rpyc.connect("127.0.0.1", 8888)
bgsrv = rpyc.utils.helpers.BgServingThread(conn)

def execute(conn, i):
    event = threading.Event()
    def cb(i):
        event.set()

    def cb2(res):
        try:
            res.value
        except Exception as e:
            event.set()     # avoid the deadlock
            print(e)        # the world should know

    # NOTE: this should be:
    #   asy = rpyc.async(conn.root.test)
    #   ret = asy(cb, i)
    # OR at least:
    #   fun = conn.root.test
    #   ret = rpyc.async(fun)(cb, i)
    ret = rpyc.async(conn.root.test)(cb, i)
    #ret.add_callback(cb2)
    print "waiting", i
    event.wait()
    print "WAITED"

i = 0
while True:
    ths = {}
    for x in range(5):
        i += 1
        th = threading.Thread(target=execute, args=(conn, i))
        th.daemon = True
        th.start()

        ths[i] = th

    for k, v in ths.iteritems():
        print "joining", k
        v.join()
        print "joined", k

conn.close()
