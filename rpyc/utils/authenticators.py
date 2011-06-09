"""
An *authenticator* is basically a callable object that takes a socket and
"authenticates" it in some way. Upon success, it must return a tuple containing 
a socket-like object and its credentials (any object), or raise an 
:class:`AuthenticationError` upon failure. There are no constraints on what the
authenticator may or may not do, for instance::

    def magic_word_authenticator(sock):
        if sock.recv(5) != "Ma6ik":
            raise AuthenticationError("wrong magic word")
        return sock, None

RPyC comes bundled with an authenticator for ``SSL`` (using certificates) 
and one for TLSLite's ``VerifierDB`` approach (username-password authentication).
These authenticators, for instance, both verify the peer's identity and wrap the 
socket with an encrypted transport (which replaces the original socket).

Authenticators are used by :class:`servers <rpyc.utils.server.Server>` to 
validate an incoming connection. Using them is pretty trivial ::

    s = ThreadedServer(...., authenticator = magic_word_authenticator)
    s.start()

"""
import os
import sys
import anydbm
from rpyc.lib import safe_import
tlsapi = safe_import("tlslite.api")
ssl = safe_import("ssl")

class AuthenticationError(Exception):
    """raised to signal a failed authentication attempt"""
    pass


class SSLAuthenticator(object):
    """An implementation of the authenticator protocol for ``SSL``. The given
    socket is wrapped by ``ssl.wrap_socket`` and is validated based on 
    certificates
    
    :param keyfile: the server's key file
    :param certfile: the server's certificate file
    :param ca_certs: the server's certificate authority file
    :param cert_reqs: the certificate requirements. By default, if ``ca_cert`` is
                      specified the requirement is set to ``CERT_REQUIRED``; 
                      otherwise it is set to ``CERT_NONE``
    :param ciphers: the list of ciphers to use, or ``None``, if you do not wish
                    to restrict the available ciphers. New in Python 2.7/3.2
    :param ssl_version: the SSL version to use
    
    Refer to `ssl.wrap_socket <http://docs.python.org/dev/library/ssl.html#ssl.wrap_socket>`_
    for more info.
    """
    
    def __init__(self, keyfile, certfile, ca_certs = None, cert_reqs = None, 
            ssl_version = None, ciphers = None):
        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs
        self.ciphers = ciphers
        if cert_reqs is None:
            if ca_certs:
                self.cert_reqs = ssl.CERT_REQUIRED
            else:
                self.cert_reqs = ssl.CERT_NONE
        else:
            self.cert_reqs = ssl.CERT_NONE
        if ssl_version is None:
            self.ssl_version = ssl.PROTOCOL_TLSv1
        else:
            self.ssl_version = ssl_version

    def __call__(self, sock):
        kwargs = dict(keyfile = self.keyfile, certfile = self.certfile,
            server_side = True, ca_certs = self.ca_certs, cert_reqs = self.cert_reqs,
            ssl_version = self.ssl_version)
        if self.ciphers is not None:
            kwargs["ciphers"] = self.ciphers
        try:
            sock2 = ssl.wrap_socket(sock, **kwargs)
        except ssl.SSLError:
            ex = sys.exc_info()[1]
            raise AuthenticationError(str(ex))
        return sock2, sock2.getpeercert()


class TlsliteVdbAuthenticator(object):
    """
    A Verifier Database authenticator, based on TLSlite's mechanisms.
    Use :file:`scripts/rpyc_vdbconf.py` to manipulate VDB files.
    """
    __slots__ = ["vdb"]
    BITS = 2048

    def __init__(self, vdb):
        self.vdb = vdb

    @classmethod
    def from_dict(cls, users):
        """factory method that creates a VDB from a dictionary mapping usernames
        to their respective passwords"""
        
        inst = cls(tlsapi.VerifierDB())
        for username, password in users.iteritems():
            inst.set_user(username, password)
        return inst

    @classmethod
    def _load_vdb_with_mode(cls, vdb, mode):
        """taken from tlslite/BaseDB.py -- patched for file mode"""
        # {{
        db = anydbm.open(vdb.filename, mode)
        try:
            if db["--Reserved--type"] != vdb.type:
                raise ValueError("Not a %s database" % (vdb.type,))
        except KeyError:
            raise ValueError("Not a recognized database")
        vdb.db = db
        # }}

    @classmethod
    def from_file(cls, filename, mode = "w"):
        """loads a VDB from file"""
        vdb = tlsapi.VerifierDB(filename)
        if os.path.exists(filename):
            cls._load_vdb_with_mode(vdb, mode)
        else:
            if mode not in "ncw":
                raise ValueError("%s does not exist but mode does not allow "
                    "writing (%r)" % (filename, mode))
            vdb.create()
        return cls(vdb)

    def sync(self):
        """sync the in-memory changes to DB"""
        self.vdb.db.sync()

    def set_user(self, username, password):
        """adds/replaces the given username and sets its password"""
        self.vdb[username] = self.vdb.makeVerifier(username, password, self.BITS)

    def del_user(self, username):
        """deletes the given username from the DB"""
        del self.vdb[username]

    def list_users(self):
        """returns a list of all usernames"""
        return self.vdb.keys()

    def __call__(self, sock):
        sock2 = tlsapi.TLSConnection(sock)
        sock2.fileno = lambda fd = sock.fileno(): fd    # tlslite omitted fileno
        try:
            sock2.handshakeServer(verifierDB = self.vdb)
        except Exception:
            ex = sys.exc_info()[1]
            raise AuthenticationError(str(ex))
        return sock2, sock2.allegedSrpUsername

