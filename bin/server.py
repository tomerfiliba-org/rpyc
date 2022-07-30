import rpyc
import time
from rpyc.utils.server import ThreadedServer


class HelloService(rpyc.Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.myfunc = None

    def exposed_sleep(self, seconds):
        return time.sleep(seconds)

    def exposed_set_myfunc(self, func_name):
        # more often than not, it is better practice to directly expose such as exposed_sleep
        whitelist = {'sleep': self.exposed_sleep}
        if func_name not in whitelist:
            raise ValueError("Not allowed value")
        else:
            self.myfunc = whitelist[func_name]

    def exposed_call_myfunc(self, *args, **kwargs):
        # remember objects returned by myfunc still must be exposed or brineable
        return self.myfunc(*args, **kwargs)


if __name__ == "__main__":
    rpyc.lib.setup_logger()
    server = ThreadedServer(HelloService, port=12345)
    server.start()
