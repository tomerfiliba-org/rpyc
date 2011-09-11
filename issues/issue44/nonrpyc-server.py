import socket
import ssl
import threading
import time

listener = socket.socket()
listener.bind(("localhost", 13388))
listener.listen(10)

def handle_sock(s):
    s2 = ssl.wrap_socket(s, server_side = True, keyfile = 'cert.key', certfile = 'cert.crt', 
        cert_reqs = ssl.CERT_NONE, ca_certs = None, ssl_version = ssl.PROTOCOL_TLSv1)
    for i in range(3):
        data = s2.recv(1000)
        s2.send(data)
    time.sleep(1)
    #s2.close()

while True:
    s, _ = listener.accept()
    t = threading.Thread(target = handle_sock, args = (s,))
    t.start()



