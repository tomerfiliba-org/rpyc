import rpyc
import os

class URL (str):
    pass

class DownloadService (rpyc.Service):
    def exposed_download_url (self, url, finished):
        a = rpyc.async(finished)
        a(URL(url))

if __name__ == '__main__':
    print os.getpid()
    from rpyc.utils.server import ThreadedServer
    serv = ThreadedServer(DownloadService, port=18812, protocol_config={"allow_all_attrs": True})
    serv.start()
