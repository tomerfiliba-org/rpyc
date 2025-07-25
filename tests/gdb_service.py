import gdb
import rpyc


class GDBService(rpyc.Service):
    def exposed_get(self):
        return gdb

    def exposed_quit(self):
        gdb.execute('quit')


if __name__ == "__main__":
    server = rpyc.OneShotServer(GDBService, port=0, protocol_config={'allow_all_attrs': True})
    gdb.write('{}\n'.format(server.port))
    gdb.flush()
    server.start()
