import threading
import socket
import select
import sys


l = threading.Lock()
listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind(("localhost", 0))
listener.listen(1)
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.connect(listener.getsockname())
s3 = listener.accept()[0]


def server():
    try:
        while True:
            if not s3.recv(100):
                s3.close()
                break
            s3.send("aaa")
    except KeyboardInterrupt:
        s3.close()


def client(name):
    try:
        while True:
            sys.stdout.write("%s acq\n" % (name,))
            try:
                l.acquire()
                sys.stdout.write("%s ACQ\n" % (name,))
                r, _, _, = select.select([s2], [], [], 0.1)
                if not r:
                    continue
                buf = s2.recv(100)
                if not buf:
                    s2.close()
                    break
                s2.send("bbb")
            finally:
                sys.stdout.write("%s rel\n" % (name,))
                l.release()
                sys.stdout.write("%s REL\n" % (name,))
    except KeyboardInterrupt:
        s2.close()

t1 = threading.Thread(target=server)
t2 = threading.Thread(target=client, args=("C1",))

t1.start()
t2.start()
client("C2")

