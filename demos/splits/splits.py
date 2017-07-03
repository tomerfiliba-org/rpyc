import sys
import rpyc
from plumbum import SshMachine
from rpyc.utils.zerodeploy import DeployedServer
from rpyc.utils.splitbrain import splitbrain

mach = SshMachine("192.168.1.117")

print sys.platform

with DeployedServer(mach) as dep:
    conn = dep.classic_connect()
    print conn.modules.sys.platform

    try:
        import posix
    except ImportError as ex:
        print ex

    with splitbrain(conn):
        import posix
        print posix.stat("/boot")

    print posix



