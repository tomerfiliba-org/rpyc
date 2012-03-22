from __future__ import with_statement
from rpyc import Service, async
from rpyc.utils.server import ThreadedServer
from threading import RLock


USERS_DB = {
    "foo" : "bar",
    "spam" : "bacon",
    "eggs" : "viking",
}
broadcast_lock = RLock()
tokens = set()


class UserToken(object):
    def __init__(self, name, callback):
        self.name = name
        self.stale = False
        self.callback = callback
        self.broadcast("* Hello %s *" % (self.name,))
        tokens.add(self)

    def exposed_say(self, message):
        if self.stale:
            raise ValueError("User token is stale")
        self.broadcast("[%s] %s" % (self.name, message))

    def exposed_logout(self):
        if self.stale:
            return
        self.stale = True
        self.callback = None
        tokens.discard(self)
        self.broadcast("* Goodbye %s *" % (self.name,))

    def broadcast(self, text):
        global tokens
        stale = set()
        with broadcast_lock:
            for tok in tokens:
                try:
                    tok.callback(text)
                except:
                    stale.add(tok)
            tokens -= stale


class ChatService(Service):
    def on_connect(self):
        self.token = None

    def on_disconnect(self):
        if self.token:
            self.token.exposed_logout()

    def exposed_login(self, username, password, callback):
        if self.token and not self.token.stale:
            raise ValueError("already logged in")
        if username in USERS_DB and password == USERS_DB[username]:
            self.token = UserToken(username, async(callback))
            return self.token
        else:
            raise ValueError("wrong username or password")


if __name__ == "__main__":
    t = ThreadedServer(ChatService, port = 19912)
    t.start()

