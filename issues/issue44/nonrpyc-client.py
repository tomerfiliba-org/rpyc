import socket
import ssl

for i in range(5000):
    if i % 100 == 0:
        print i
    sock = ssl.wrap_socket(socket.socket(), server_side = False, keyfile = 'cert.key', 
        certfile = 'cert.crt', cert_reqs = ssl.CERT_NONE, ca_certs = None, \
        ssl_version = ssl.PROTOCOL_TLSv1)
    sock.connect(("localhost", 13388))
    for text in ["hello world", "foobar", "spam and eggs"]:
        sock.send(text)
        data = sock.recv(1000)
        assert data == text

