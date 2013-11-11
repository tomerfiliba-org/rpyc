"""
.. versionadded:: 3.3

Requires [plumbum](http://plumbum.readthedocs.org/)
"""
from __future__ import with_statement
import rpyc
import socket
from rpyc.core.service import VoidService
from rpyc.core.stream import SocketStream
from os import path
from inspect import getfile
try:
    from plumbum import local, ProcessExecutionError
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
            if fn == "__pycache__" or (fn.endswith(".pyc") or os.path.exists(fn[:-1])):
                os.remove(os.path.join(dirpath, fn))
except Exception:
    pass

sys.path.insert(0, here)
from %(module)s import %(server)s as ServerCls
%(serviceClsImportStr)s

t = ServerCls(%(clsName)s, hostname = "localhost", port = 0, reuse_addr = True)
sys.stdout.write("%%s\n" %% (t.port,))
sys.stdout.flush()

try:
    thd = Thread(target = t.start)
    thd.setDaemon(True)
    thd.start()
    sys.stdin.read()
finally:
    t.close()
    thd.join(2)
"""

class BaseDeployedServer(object):
    """
    - Base class for deployed server 
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
    """
    
    def __init__(self, remote_machine, server_class = "rpyc.utils.server.ThreadedServer"):
        self.proc = None
        self.tun = None
        self.remote_port = None        
        self.remote_machine = remote_machine
        self.remote_machine_type = remote_machine.__class__.__name__
        self.srvModuleName, self.srvClsName = server_class.rsplit(".", 1)
        self._tmpdir_ctx = remote_machine.tempdir()
        self._tmpdir_path = self._tmpdir_ctx.__enter__()        
        self._script_path = ( self._tmpdir_path / "deployed-rpyc.py")
        #Copy modules dir
        if self.remote_machine_type ==  "SshMachine":
            rpyc_root = local.path(rpyc.__file__).dirname
        else:
            rpyc_root = local.path(rpyc.__file__).up(2)
        copy(rpyc_root, self._tmpdir_path)
        #create script        

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
            self._tmpdir_path = None
    
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
    def _executeRemoteScript(self):
        """ Executes deployed rpyc script on destination """
        self.proc = self.remote_machine.python.popen(self._script_path, new_session = True)
    def _getRemotePort(self):
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
            raise ProcessExecutionError(self.proc.argv, self.proc.returncode, line + stdout, stderr)
    def _createTunnel(self):        
        if hasattr(self.remote_machine, "connect_sock"):
            # Paramiko: use connect_sock() instead of tunnels
            self.local_port = None
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("localhost", 0))
            self.local_port = s.getsockname()[1]
            s.close()
            self.tun = self.remote_machine.tunnel(self.local_port, self.remote_port)          

class DeployedServer(BaseDeployedServer):
    def __init__(self, remote_machine, server_class = "rpyc.utils.server.ThreadedServer"):
        BaseDeployedServer.__init__(self, remote_machine, server_class)
        self._script_path.write(SERVER_SCRIPT%{ "module": self.srvModuleName, 
                                                                            "server" : self.srvClsName,                                                                            
                                                                            "serviceClsImportStr": "from rpyc import SlaveService",
                                                                            "clsName" : "SlaveService"                                                                             
                                                                         })                            
        self._executeRemoteScript()
        self._getRemotePort()
        self._createTunnel()

class CustomDeployedServer(BaseDeployedServer):
    """ 
    This deployed server uses service model. Service class should be located in different file.
    CustomDeployedServer copies the file in which service is located and appropriately modifies the script that is run on remote server.
    Custom service class should also be imported in the file where CustomDeployedServer object is used. 
    For example: 
              from rpyc_test_service import TestService
              mach = SshMachine(<hostName>, user=<userName>)
              server = CustomDeployedServer(remote_machine=mach, serviceCls = TestService)
              conn1 = server.connect()
    :param serviceCls: class of the custom service
    """
    def __init__(self, remote_machine, server_class = "rpyc.utils.server.ThreadedServer", serviceCls = None):
        BaseDeployedServer.__init__(self, remote_machine, server_class)
        serviceClsPath = local.path(getfile(serviceCls).replace(".pyc",".py"))
        copy(serviceClsPath, self._tmpdir_path)
        self._script_path.write(SERVER_SCRIPT%{ "module": self.srvModuleName, 
                                                                            "server" : self.srvClsName,                                                                            
                                                                            "serviceClsImportStr": "import "+serviceCls.__module__,
                                                                            "clsName" : serviceCls.__module__+"."+serviceCls.__name__
                                                                         })        
        self._executeRemoteScript()
        self._getRemotePort()        
        self._createTunnel()
                                  
        
        
class MultiServerDeployment(object):
    """
    An 'aggregate' server deployment to multiple SSH machine. It deploys RPyC to each machine
    separately, but lets you manage them as a single deployment.
    """
    def __init__(self, remote_machines, server_class = "rpyc.utils.server.ThreadedServer"):
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



