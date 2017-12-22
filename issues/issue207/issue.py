import logging
from rpyc.utils.zerodeploy import DeployedServer
from plumbum.machines.paramiko_machine import ParamikoMachine
from paramiko import AutoAddPolicy

logging.basicConfig(level=logging.DEBUG)

p = ParamikoMachine("localhost", missing_host_policy=AutoAddPolicy())
s = DeployedServer(p)
r = s.classic_connect()

# Configure logging, so that remote logging events are correctly
# passed to the local logger to be handled.
rlogger = r.modules.logging.getLogger()
rlogger.parent=logging.getLogger()

# If this is set to a log level higher than DEBUG, the bug doesn't reproduce.
rlogger.setLevel(logging.DEBUG)
rlogger.foo
rlogger.addHandler(logging.NullHandler)
