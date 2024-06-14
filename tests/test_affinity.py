import sys
import time
import unittest
from tests import support
import rpyc


class Test_Affinity(unittest.TestCase):
    """To find race conditions we vary processor affinity (CPU pinning) settings.

    GIL tends to context switch more frequently when more CPU cores are available. By running binding this PID
    to one CPU core, more ticks will occur between each context switch. Increasing the number of CPU cores we are bound to
    will run be able to test RPyC with more frequent context switching. The aim is to find contention between threads for
    the socket that result in undesired behavior (e.g. a reply never making it to the right thread).

    Python Thread Visualization: http://www.dabeaz.com/GIL/gilvis/fourthread.html
    """
    @classmethod
    def setUpClass(cls):
        """Construct the a copy of ClassicServer that embeds a sleep(0) into _dispatch and set affinity"""
        cls._orig_func = rpyc.core.protocol.Connection._dispatch

        def _sleepy_dispatch(self, data):
            time.sleep(0.0)
            return cls._orig_func(self, data)
        setattr(rpyc.core.protocol.Connection, '_dispatch', _sleepy_dispatch)
        cls.cfg = {'sync_request_timeout': 5}
        if sys.platform != "linux":
            print("Running Test_Affinity is less productive on non-linux systems...")
        try:
            cls._skip = None
            cls._os = None
            cls._supported = True
            cls._os = support.import_module('os', fromlist=('sched_setaffinity', 'sched_getaffinity'))
            cls._orig_affinity = cls._os.sched_getaffinity(0)
        except unittest.SkipTest as skip:
            cls._skip = skip
            cls._supported = False
            cls._orig_affinity = None

    @classmethod
    def tearDownClass(cls):
        setattr(rpyc.core.protocol.Connection, '_dispatch', cls._orig_func)

    def setUp(self):
        self._os.sched_setaffinity(0, {0, })
        self.conn = rpyc.connect_thread(rpyc.ClassicService, self.cfg, rpyc.ClassicService, self.cfg)
        self.bg_threads = [rpyc.BgServingThread(self.conn) for i in range(3)]

    def tearDown(self):
        for t in self.bg_threads:
            t.stop()
        self.bg_threads = []
        self.conn.close()
        self.conn = None
        self._reset_affinity()

    def _time_execute_sleep(self):
        """returns time to execute 0.3s worth of sleeping"""
        t0 = time.time()
        self.conn.execute("import time")
        for p in (0, 0.1, 0.2):
            self.conn.execute(f"time.sleep({p})")
        return time.time() - t0

    def _reset_affinity(self):
        if self._os is not None:
            return self._os.sched_setaffinity(0, self._orig_affinity)

    def test_pinned_to_0(self):
        """test behavior with processor affinity set such that this process is pinned to 0"""
        if self._skip:
            raise self._skip
        max_elapsed_time = self.cfg['sync_request_timeout']
        elapsed_time = self._time_execute_sleep()
        self.assertLess(elapsed_time, max_elapsed_time)
        self.assertIn('count=0', repr(self.conn._recvlock))
