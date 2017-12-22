


async_callback = rpyc.async(callback)
x = 0
while x < 1000:
    async_callback({ "runtime" : time.time()})
    time.sleep(0.5)
    x += 1
