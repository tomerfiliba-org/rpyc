import logging
import rpyc

def finished (self, url):
    print "Finished."

if __name__ == '__main__':
    url = "http://www.car-it.com/wp-content/uploads/2014/02/13C1150_092.jpg"
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger(__name__)
    con = rpyc.connect("localhost", port=18812, config={"allow_all_attrs": True, "logger": log})
    con.root.download_url(url, finished)
    # Keep alive.
    while True:
        pass
