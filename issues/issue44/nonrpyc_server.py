import socket
import select
import ssl
import threading
import time

files = [open("/tmp/rpyc-test-%d" % (i,), "w") for i in range(1000)]
sockets = [socket.socket() for i in range(100)]

listener = socket.socket()
assert listener.fileno() > 1024

listener.bind(("localhost", 13388))
listener.listen(10)

def handle_sock(s):
    s2 = ssl.wrap_socket(s, server_side = True, keyfile = 'cert.key', certfile = 'cert.crt', 
        cert_reqs = ssl.CERT_NONE, ca_certs = None, ssl_version = ssl.PROTOCOL_TLSv1)
    select.select([s2], [], [], 1)
    for i in range(3):
        data = s2.recv(1000)
        s2.send(data)
    time.sleep(1)
    #s2.close()

while True:
    s, _ = listener.accept()
    assert s.fileno() > 1024
    t = threading.Thread(target = handle_sock, args = (s,))
    t.start()



