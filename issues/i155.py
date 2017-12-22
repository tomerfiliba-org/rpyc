from rpyc.utils.zerodeploy import DeployedServer
from rpyc.utils.classic import teleport_function
from plumbum.machines.ssh_machine import SshMachine

if __name__ == '__main__':
    machine = SshMachine('localhost')
    server = DeployedServer(machine)
    conn = server.classic_connect()

    def f(x, y):
        import os
        return (os.getpid() + y) * x

    r_f = teleport_function(conn, f)

    print f(1, 2)
    print r_f(1, 2)
