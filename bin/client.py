import time
import rpyc
import logging

DEFAULT_SERVER_PORT = rpyc.utils.classic.DEFAULT_SERVER_PORT
SlaveService = rpyc.utils.classic.SlaveService
rpyc.setup_logger()
config = {'logger': logging.getLogger()}
conn = rpyc.utils.factory.connect("127.0.0.1", DEFAULT_SERVER_PORT, SlaveService, config=config, ipv6=False, keepalive=False)

bg_threads = []

for i in range(3):
    bg_threads.append(rpyc.BgServingThread(conn))

if __name__ == "__main__":
    t0 = time.time()
    conn.execute("import time")
    print(time.time() - t0)
