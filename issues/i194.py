from plumbum import SshMachine
from rpyc.utils.zerodeploy import MultiServerDeployment

m1 = SshMachine("localhost")
m2 = SshMachine("localhost")
m3 = SshMachine("localhost")

dep = MultiServerDeployment([m1, m2, m3], '')
conn1, conn2, conn3 = dep.classic_connect_all()

# ...

dep.close()
