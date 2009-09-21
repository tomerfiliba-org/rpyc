"""
functions for distributing package and modules across hosts
"""
import inspect
from Files import upload_dir
from Builtins import reload


__all__ = ["upload_package", "update_module"]

def upload_package(conn, module, remotepath = None):
    """
    uploads the given package to the server, storing it in `remotepath`. if 
    remotepath is None, it defaults to the server's site-packages. if the package
    already exists, it is overwritten.
    usage:
        import xml
        upload_package(conn, xml)
    """
    if remotepath is None:
        remotepath = conn.modules["distutils.sysconfig"].get_python_lib()
    localpath = os.path.dirname(module.__file__)
    upload_dir(conn, localpath, remotepath, [".py", ".pyd", ".dll", ".so", ".zip"])

def update_module(conn, module):
    """
    updates an existing module on the server. the local module is transfered to the
    server, overwriting the old one, and is reloaded. 
    usage:
        import xml.dom.minidom
        update_module(conn, xml.dom.minidom)
    """
    remote_module = conn.modules[module.__name__]
    local_file = inspect.getsourcefile(module)
    remote_file = inspect.getsourcefile(remote_module)
    upload_file(conn, local_filem, remote_file)
    reload(remote_module)