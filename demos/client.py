import time
import rpyc

conn = rpyc.classic.connect("localhost")

bg_threads = []

for i in range(3):
    bg_threads.append(rpyc.BgServingThread(conn))

if __name__ == "__main__":
    t0 = time.time()
    conn.execute("import time")
    print(time.time() - t0)
