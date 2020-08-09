import rpyc
from time import sleep


class MyClient(object):

    def __init__(self):
        self.conn = rpyc.connect("localhost", 18000)
        self.bgsrv = rpyc.BgServingThread(self.conn)
        self.root = self.conn.root
        self.service = self.root.MyService("/tmp/test.txt", self.on_event)  # create a filemon

    def on_event(self, oldstat, newstat):
        print("file changed")
        print("    old stat: %s" % (oldstat,))
        print("    new stat: %s" % (newstat,))

    def close(self):
        self.service.stop()
        self.bgsrv.stop()
        self.conn.close()


if __name__ == "__main__":

    client = MyClient()
    sleep(10)
    client.close()
