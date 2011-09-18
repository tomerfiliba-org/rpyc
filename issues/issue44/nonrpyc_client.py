import socket
import ssl

for i in range(5000):
    if i % 100 == 0:
        print i
    sock = socket.socket()
    sock.connect(("localhost", 13388))
    sock2 = ssl.wrap_socket(sock, server_side = False, keyfile = 'cert.key', 
        certfile = 'cert.crt', cert_reqs = ssl.CERT_NONE, ca_certs = None, 
        ssl_version = ssl.PROTOCOL_TLSv1)
    
    for text in ["hello world", "foobar", "spam and eggs"]:
        sock2.send(text)
        data = sock2.recv(1000)
        assert data == text
    #sock.close()

