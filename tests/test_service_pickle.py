from __future__ import print_function
import sys
import pickle  # noqa
import timeit
import rpyc
import unittest
import cfg_tests
try:
    import pandas as pd
    import numpy as np
    _pampy_import_failed = False
except Exception:
    pd = None
    np = None
    _pampy_import_failed = True


DF_ROWS = 2000
DF_COLS = 2500


class MyService(rpyc.Service):
    on_connect_called = False
    on_disconnect_called = False

    def on_connect(self, conn):
        self.on_connect_called = True

    def on_disconnect(self, conn):
        self.on_disconnect_called = True

    def exposed_write_data(self, dataframe):
        rpyc.classic.obtain(dataframe)

    def exposed_get(self):
        return np.random.rand(3, 3)

    def exposed_ping(self):
        return "pong"


@unittest.skipIf(_pampy_import_failed, "Pandas & numpy are not available")
class TestServicePickle(unittest.TestCase):
    """Issues #323 and #329 showed for large objects there is an excessive number of round trips.

    This test case should check the interrelations of
        + MAX_IO_CHUNK
        + min twrite
        + occurrence rate of socket timeout for other clients
    """
    config = {}

    def setUp(self):
        self.cfg = {'allow_pickle': True}
        self.server = rpyc.utils.server.ThreadedServer(MyService, port=0, protocol_config=self.cfg.copy())
        self.server.logger.quiet = False
        self.thd = self.server._start_in_thread()
        self.conn = rpyc.connect("localhost", self.server.port, config=self.cfg)
        self.conn2 = rpyc.connect("localhost", self.server.port, config=self.cfg)
        # globals are made available to timeit, prepare them
        cfg_tests.timeit['conn'] = self.conn
        cfg_tests.timeit['conn2'] = self.conn2
        cfg_tests.timeit['df'] = pd.DataFrame(np.random.rand(DF_ROWS, DF_COLS))

    def tearDown(self):
        self.conn.close()
        self.server.close()
        self.thd.join()
        cfg_tests.timeit.clear()

    def test_dataframe_pickling(self):
        # the proxy will sync w/ the pickle handle and default proto and provide this as the argument to pickle.load
        # By timing how long w/ out any round trips pickle.dumps and picke.loads takes, the overhead of RPyC protocol
        # can be found

        rpyc.core.channel.Channel.COMPRESSION_LEVEL = 1
        # rpyc.core.stream.SocketStream.MAX_IO_CHUNK = 8000
        level = rpyc.core.channel.Channel.COMPRESSION_LEVEL
        max_chunk = rpyc.core.stream.SocketStream.MAX_IO_CHUNK
        repeat = 3
        number = 1
        pickle_stmt = 'pickle.loads(pickle.dumps(cfg_tests.timeit["df"]))'
        write_stmt = 'rpyc.lib.spawn(cfg_tests.timeit["conn"].root.write_data, cfg_tests.timeit["df"]); '
        write_stmt += '[cfg_tests.timeit["conn2"].root.ping() for i in range(30)]'
        # write_stmt = 'cfg_tests.timeit["conn"].root.write_data(cfg_tests.timeit["df"])'
        t = timeit.Timer(pickle_stmt, globals=globals())
        tpickle = min(t.repeat(repeat, number))
        t = timeit.Timer(write_stmt, globals=globals())
        twrite = min(t.repeat(repeat, number))

        headers = ['sample', 'tpickle', 'twrite', 'bytes', 'level', 'max_chunk']  # noqa
        data = [repeat, tpickle, twrite, sys.getsizeof(cfg_tests.timeit['df']), level, max_chunk]
        data = [str(d) for d in data]
        # print(','.join(headers), file=open('/tmp/time.csv', 'a'))
        # print(','.join(data), file=open('/tmp/time.csv', 'a'))


if __name__ == "__main__":
    unittest.main()
