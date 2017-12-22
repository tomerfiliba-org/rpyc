import rpyc
import time

rpc = rpyc.connect("localhost", 4158)

# test to verify connection
rpc.root.func()

time.sleep(1000)
