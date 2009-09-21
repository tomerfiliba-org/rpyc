"""
authenticators: the server instance accepts an authenticator object,
which is basically any callable (i.e., a function) that takes the newly
connected socket and "authenticates" it. 

the authenticator should return a socket-like object with its associated 
credentials (a tuple), or raise AuthenticationError if it fails.

a very trivial authenticator might be

    def magic_word_authenticator(sock):
        if sock.recv(5) != "Ma6ik":
            raise AuthenticationError("wrong magic word")
        return sock, None
    
    s = ThreadedServer(...., authenticator = magic_word_authenticator)

your authenticator can return any socket-like object. for instance, it may 
authenticate the client and return a TLS/SSL-wrapped socket object that 
encrypts the transport.

the credentials returned alongside with the new socket can be any object.
it will be stored in the rpyc connection configruation under the key
"credentials", and may be used later by the service logic. if no credentials
are applicable, just return None as in the example above.

rpyc includes integration with tlslite, a TLS/SSL library:
the VdbAuthenticator class authenticates clients based on username-password 
pairs.
"""
from rpyc.utils.lib import safe_import
tlsapi = safe_import("tlslite.api")


class AuthenticationError(Exception):
    pass


class VdbAuthenticator(object):
    __slots__ = ["vdb"]
    BITS = 2048
    
    def __init__(self, vdb):
        self.vdb = vdb
    
    @classmethod
    def from_users(cls, users): 
        inst = cls(tlsapi.VerifierDB())
        for username, password in users.iteritems():
            inst.set_user(username, password)
        return inst
    
    @classmethod
    def from_file(cls, filename):
        vdb = tlsapi.VerifierDB(filename)
        if os.path.exists(filename):
            vdb.open()
        else:
            vdb.create()
        return cls(vdb)
    
    def set_user(self, username, password):
        self.vdb[username] = self.vdb.makeVerifier(username, password, self.BITS)
    
    def __call__(self, sock):
        sock2 = tlsapi.TLSConnection(sock)
        sock2.fileno = lambda fd=sock.fileno(): fd    # tlslite omitted fileno
        try:
            sock2.handshakeServer(verifierDB = self.vdb)
        except Exception, ex:
            raise AuthenticationError(str(ex))
        return sock2, sock2.allegedSrpUsername







