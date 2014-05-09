"""
.. versionadded:: 3.3

Requires [plumbum](http://plumbum.readthedocs.org/)
"""
from __future__ import with_statement
import sys
import rpyc
import socket
from rpyc.lib.compat import BYTES_LITERAL
from rpyc.core.service import VoidService
from rpyc.core.stream import SocketStream
try:
    from plumbum import local, ProcessExecutionError, CommandNotFound
    from plumbum.path import copy
except ImportError:
    import inspect
    if any("sphinx" in line[1] or "docutils" in line[1] or "autodoc" in line[1] for line in inspect.stack()):
        # let the sphinx docs be built without requiring plumbum installed
        pass
    else:
        raise


SERVER_SCRIPT = r"""\
import sys
import os
import atexit
import shutil
from threading import Thread

here = os.path.dirname(__file__)
os.chdir(here)

def rmdir():
    shutil.rmtree(here, ignore_errors = True)
atexit.register(rmdir)

try:
    for dirpath, _, filenames in os.walk(here):
        for fn in filenames:
            if fn == "__pycache__" or (fn.endswith(".pyc") and os.path.exists(fn[:-1])):
                os.remove(os.path.join(dirpath, fn))
except Exception:
    pass

sys.path.insert(0, here)
from $MODULE$ import $SERVER$ as ServerCls
from rpyc import SlaveService

logger = None
$EXTRA_SETUP$

t = ServerCls(SlaveService, hostname = "localhost", port = 0, reuse_addr = True, logger = logger)
thd = Thread(target = t.start)
thd.setDaemon(True)
thd.start()

sys.stdout.write("%s\n" % (t.port,))
sys.stdout.flush()

try:
    sys.stdin.read()
finally:
    t.close()
    thd.join(2)
"""

class DeployedServer(object):
    """
    Sets up a temporary, short-lived RPyC deployment on the given remote machine. It will: 
    
    1. Create a temporary directory on the remote machine and copy RPyC's code 
       from the local machine to the remote temporary directory.
    2. Start an RPyC server on the remote machine, binding to an arbitrary TCP port,
       allowing only in-bound connections (``localhost`` connections). The server reports the 
       chosen port over ``stdout``.
    3. An SSH tunnel is created from an arbitrary local port (on the local host), to the remote 
       machine's chosen port. This tunnel is authenticated and encrypted.
    4. You get a ``DeployedServer`` object that can be used to connect to the newly-spawned server.
    5. When the deployment is closed, the SSH tunnel is torn down, the remote server terminates 
       and the temporary directory is deleted.
    
    :param remote_machine: a plumbum ``SshMachine`` or ``ParamikoMachine`` instance, representing 
                           an SSH connection to the desired remote machine
    :param server_class: the server to create (e.g., ``"ThreadedServer"``, ``"ForkingServer"``)
    :param extra_setup: any extra code to add to the script
    """
    
    def __init__(self, remote_machine, server_class = "rpyc.utils.server.ThreadedServer", extra_setup = "", python_executable=None):
        self.proc = None
        self.tun = None
        self.remote_machine = remote_machine
        self._tmpdir_ctx = None
        
        rpyc_root = local.path(rpyc.__file__).up()
        self._tmpdir_ctx = remote_machine.tempdir()
        tmp = self._tmpdir_ctx.__enter__()
        copy(rpyc_root, tmp / "rpyc")
        
        script = (tmp / "deployed-rpyc.py")
        modname, clsname = server_class.rsplit(".", 1)
        script.write(SERVER_SCRIPT.replace("$MODULE$", modname).replace("$SERVER$", clsname).replace("$EXTRA_SETUP$", extra_setup))
        if python_executable:
            cmd = remote_machine[python_executable]
        else:
            major = sys.version_info[0]
            minor = sys.version_info[1]
            cmd = None
            for opt in ["python%s.%s" % (major, minor), "python%s" % (major,)]:
                try:
                    cmd = remote_machine[opt]
                except CommandNotFound:
                    pass
                else:
                    break
            if not cmd:
                cmd = remote_machine.python
        
        self.proc = cmd.popen(script, new_session = True)
        
        line = ""
        try:
            line = self.proc.stdout.readline()
            self.remote_port = int(line.strip())
        except Exception:
            try:
                self.proc.terminate()
            except Exception:
                pass
            stdout, stderr = self.proc.communicate()
            raise ProcessExecutionError(self.proc.argv, self.proc.returncode, BYTES_LITERAL(line) + stdout, stderr)
        
        if hasattr(remote_machine, "connect_sock"):
            # Paramiko: use connect_sock() instead of tunnels
            self.local_port = None
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("localhost", 0))
            self.local_port = s.getsockname()[1]
            s.close()
            self.tun = remote_machine.tunnel(self.local_port, self.remote_port)

    def __del__(self):
        self.close()
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()

    def close(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None
        if self.tun is not None:
            try:
                self.tun.close()
            except Exception:
                pass
            self.tun = None
        if self._tmpdir_ctx is not None:
            try:
                self._tmpdir_ctx.__exit__(None, None, None)
            except Exception:
                pass
            self._tmpdir_ctx = None
    
    def connect(self, service = VoidService, config = {}):
        """Same as :func:`connect <rpyc.utils.factory.connect>`, but with the ``host`` and ``port`` 
        parameters fixed"""
        if self.local_port is None:
            # ParamikoMachine
            stream = SocketStream(self.remote_machine.connect_sock(self.remote_port))
            return rpyc.connect_stream(stream, service = service, config = config)
        else:
            return rpyc.connect("localhost", self.local_port, service = service, config = config)
    
    def classic_connect(self):
        """Same as :func:`classic.connect <rpyc.utils.classic.connect>`, but with the ``host`` and 
        ``port`` parameters fixed"""
        if self.local_port is None:
            # ParamikoMachine
            stream = SocketStream(self.remote_machine.connect_sock(self.remote_port))
            return rpyc.classic.connect_stream(stream)
        else:
            return rpyc.classic.connect("localhost", self.local_port)


class MultiServerDeployment(object):
    """
    An 'aggregate' server deployment to multiple SSH machine. It deploys RPyC to each machine
    separately, but lets you manage them as a single deployment.
    """
    def __init__(self, remote_machines, server_class = "ThreadedServer"):
        self.remote_machines = remote_machines
        # build the list incrementally, so we can clean it up if we have an exception
        self.servers = [DeployedServer(mach, server_class) for mach in remote_machines]
    
    def __del__(self):
        self.close()
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()
    def __iter__(self):
        return iter(self.servers)
    def __len__(self):
        return len(self.servers)
    def __getitem__(self, index):
        return self.servers[index]
    
    def close(self):
        while self.servers:
            s = self.servers.pop(0)
            s.close()
    
    def connect_all(self, service = VoidService, config = {}):
        """connects to all deployed servers; returns a list of connections (order guaranteed)"""
        return [s.connect(service, config) for s in self.servers]
    def classic_connect_all(self):
        """connects to all deployed servers using classic_connect; returns a list of connections (order guaranteed)"""
        return [s.classic_connect() for s in self.servers]



