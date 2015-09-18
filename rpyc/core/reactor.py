import os
import select
import threading


class SelectReactor(object):
    TIMEOUT = 0.5 if os.name == "nt" else None

    def __init__(self):
        self._active = False
        self._readfds = set()

    def register_read(self, fileobj):
        self._readfds.append(fileobj)

    def run(self):
        self._active = True
        while self._active:
            rlist, _, _ = select.select(self._readfds, (), (), self.TIMEOUT)
            for fileobj in rlist:
                data = fileobj.recv(16000)
                if not data:
                    fileobj.close()
                    self._readfds.discard(fileobj)


_reactor = SelectReactor()


def _reactor_thread():
    pass


_thd = None


def start_reactor():
    global _thd
    if _thd is None:
        raise ValueError("already started")
    _thd = threading.Thread("rpyc reactor thread", target=_reactor_thread)
    _thd.setDaemon(True)
    _thd.start()
