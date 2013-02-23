from __future__ import with_statement
import rpyc
import socket
from contextlib import contextmanager
try:
    from plumbum import local, ProcessExecutionError
    from plumbum.utils import copy, delete
    from rpyc.core.service import VoidService
except ImportError:
    import inspect
    if any("sphinx" in line[1] or "docutils" in line[1] or "autodoc" in line[1] for line in inspect.stack()):
        # let the sphinx docs be built without requiring plumbum installed
        VoidService = None
    else:
        raise


class DeployedServer(object):
    """
    Represents a deployed RPyC server. Use the ``connect`` or ``classic_connect`` 
    methods to connect to this server. Once the :func:`deployment <rpyc.utils.zerodeploy.deployment>`
    is exited, the deployed server will be shut down automatically (killing any active 
    connection)
    """
    
    def __init__(self, local_port):
        self.local_port = local_port
    def connect(self, service = VoidService, config = {}):
        """Same as :func:`connect <rpyc.utils.factory.connect>`, but with the ``host`` and ``port`` 
        parameters fixed"""
        return rpyc.connect("localhost", self.local_port, service = service, config = config)
    def classic_connect(self):
        """Same as :func:`classic.connect <rpyc.utils.classic.connect>`, but with the ``host`` and 
        ``port`` parameters fixed"""
        return rpyc.classic.connect("localhost", self.local_port)

SERVER_SCRIPT = r"""
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import sys
t = ThreadedServer(SlaveService, hostname = "localhost", port = 0, reuse_addr = True)
sys.stdout.write("%s\n" % (t.port,))
sys.stdout.flush()
t.start()
"""

@contextmanager
def deployment(remote_machine):
    """Sets up a temporary, short-lived RPyC deployment on the given remote machine. 
    A deployment:
    
    1. Creates a temporary directory on the remote machine, and copies RPyC's code 
       from the local machine to the remote temporary directory.
    2. Starts an RPyC server on the remote machine, binding to an arbitrary TCP port,
       allowing only in-bound connections (connections from the same machine). 
       The server reports the chosen port over ``stdout``.
    3. An SSH tunnel is created from a local port on the local host, to the remote 
       machine's chosen TCP port. This tunnel is authenticated and encrypted.
    4. The deployment returns a :class:`DeployedServer <rpyc.utils.zerodeploy.DeployedServer>` 
       object, which can be used to connect to the newly-spawned server.
    5. When the deployment context is exited, the SSH tunnel is torn down, the remote
       server is terminated and the temporary directory deleted.
    
    :param remote_machine: a ``plumbum.SshMachine`` instance, representing an SSH 
                           connection to the desired remote machine
    """
    RPYC_ROOT = local.path(rpyc.__file__).dirname
    
    with remote_machine.tempdir() as tmp:
        copy(RPYC_ROOT, tmp)
        delete(tmp // ".pyc", tmp // "*/.pyc")
        with remote_machine.cwd(tmp):
            with remote_machine.env(PYTHONPATH = remote_machine.env.get("PYTHONPATH", "") + ":%s" % (tmp,)):
                proc = (remote_machine.python << SERVER_SCRIPT).popen()
        
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

