from __future__ import with_statement
from contextlib import contextmanager
from plumbum import local, ProcessExecutionError
from plumbum.utils import copy, delete
from rpyc.core.service import VoidService
import rpyc
import socket


RPYC_ROOT = local.path(rpyc.__file__).dirname

SERVER_SCRIPT = r"""
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import sys
t = ThreadedServer(SlaveService, hostname = "localhost", port = 0, reuse_addr = True)
sys.stdout.write("%s\n" % (t.port,))
sys.stdout.flush()
t.start()
"""

class DeployedServer(object):
    def __init__(self, local_port):
        self.local_port = local_port
    def connect(self, service = VoidService, config = {}):
        return rpyc.connect("localhost", self.local_port, service = service, config = config)
    def classic_connect(self):
        return rpyc.classic.connect("localhost", self.local_port)

@contextmanager
def deployment(remote_machine, code = SERVER_SCRIPT):
    with remote_machine.tempdir() as tmp:
        copy(RPYC_ROOT, tmp)
        delete(tmp // ".pyc", tmp // "*/.pyc")
        with remote_machine.cwd(tmp):
            with remote_machine.env(PYTHONPATH = remote_machine.env.get("PYTHONPATH", "") + ":%s" % (tmp,)):
                proc = (remote_machine.python << code).popen()
        
        line = ""
        try:
            line = proc.stdout.readline()
            remote_port = int(line.strip())
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            stdout, stderr = proc.communicate()
            raise ProcessExecutionError(proc.argv, proc.returncode, line + stdout, stderr)
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("localhost", 0))
        local_port = s.getsockname()[1]
        s.close()
        
        with remote_machine.tunnel(local_port, remote_port) as tun:
            try:
                yield DeployedServer(local_port)
            finally:
                try:
                    proc.kill()
                except Exception:
                    pass

