import rpyc


class MyService(rpyc.Service):
    def exposed_foo(self):
        return 18



if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    from rpyc.utils.authenticators import SSLAuthenticator
    server = ThreadedServer(MyService, port = 13388, 
        authenticator = SSLAuthenticator("cert.key", "cert.crt"),
    )
    server.start()
