import rpyc


class RemoteFSService(rpyc.Service):
    def open(self, filename, mode = "r"):
        pass
    def listdir(self, path):
        pass
    def mkdir(self, path):
        pass
    def stat(self, path):
        pass
    def rmdir(self, path):
        pass

