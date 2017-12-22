from connection import Connection, Channel, SocketStream, Service
import time


def main():
    stream = SocketStream.connect("localhost", 18861)
    c = Connection(Service, Channel(stream), {})

    while True:
        start = time.time()
        seq = c.root.ping_test()
        delta = time.time() - start
        print("{} {}".format(seq, delta))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
