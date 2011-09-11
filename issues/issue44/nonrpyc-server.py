import socket
import ssl
import threading

listener = socket.socket()
listener = ssl.wrap_socket(listener, server_side = True, keyfile = 'cert.key', certfile = 'cert.crt', 
    cert_reqs = ssl.CERT_NONE, ca_certs = None, ssl_version = ssl.PROTOCOL_TLSv1)
listener.bind(("localhost", 13388))
listener.listen(10)

def handle_sock(sock):
    data = sock.recv(1000)
    sock.send(data)
    sock.close()

while True:
    s, _ = listener.accept()
    t = threading.Thread(target = handle_sock, args = (s,))
    t.start()



