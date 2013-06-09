import sys
import rpyc
from plumbum import SshMachine
from rpyc.utils.zerodeploy import deployment
from rpyc.utils.splitbrain import splitbrain

mach = SshMachine("192.168.1.117")

print sys.platform

with deployment(mach) as dep:
    conn = dep.classic_connect()
    print conn.modules.sys.platform
    
    try:
        import posix
    except ImportError:
        pass
    
    with splitbrain(conn):
        import posix
        posix.stat


