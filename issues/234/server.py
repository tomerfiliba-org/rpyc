import rpyc

class TestObject(object):
    def __init__(self):
        self.intvalue = 123
        self.stringvalue = "test string!"
        self.otherobj = None

class TestService(rpyc.Service):
    def on_connect(self):
        print('Got connection')

    def exposed_fetch_stuff(self):
        values = []
        for i in range(20):
            x = TestObject()
            x.intvalue = i
            values.append(x)

        return values

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(TestService, port=18861,
                    protocol_config = {'allow_all_attrs':True,
                    'allow_pickle':True,
                    'allow_setattr':True,
                    'allow_public_attrs':True})
    t.start()
