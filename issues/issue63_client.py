import rpyc
import time

count = 0

def callbackFunc(x):
    global count
    count += 1
    print x, time.time()

if __name__ == "__main__":
    conn = rpyc.connect("localhost", 12000)
    #rpyc.BgServingThread.SERVE_INTERVAL = 0.01
    rpyc.BgServingThread.SLEEP_INTERVAL = 0.0001
    bgsrv = rpyc.BgServingThread(conn)

    test = conn.root.RemoteCallbackTest(callbackFunc)
    print test
    test.start()
    print "doing other things while the callback is being called"
    while count < 100:
        time.sleep(0.1)
    print "done"


