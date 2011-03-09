import os
import tempfile
import shutil
from nose import SkipTest
import rpyc

class Test_Remoting(object):
    def __init__(self):
        pass

    def setup(self):
        self.conn = rpyc.classic.connect_thread()
    
    def teardown(self):
        self.conn.close()
    
    def test_files(self):
        base = tempfile.mkdtemp()
        base1 = os.path.join(base, "1")
        base2 = os.path.join(base, "2")
        base3 = os.path.join(base, "3")
        os.mkdir(base1)
        for i in range(10):
            open(os.path.join(base1, "foofoo%d" % (i,)), "w")
        os.mkdir(os.path.join(base1, "somedir1"))
        
        rpyc.classic.upload(self.conn, base1, base2)
        assert os.listdir(base1) == os.listdir(base2)
        
        rpyc.classic.download(self.conn, base2, base3)
        assert os.listdir(base2) == os.listdir(base3)
        
        shutil.rmtree(base)
    
    def test_distribution(self):
        print "TODO: upload package"
        print "TODO: update module"
        
    def test_interactive(self):
        raise SkipTest("Need to be manually")
        print "type Ctrl+D to exit (Ctrl+Z on Windows)"
        rpyc.classic.interact(self.conn)
    
    def test_post_mortem(self):
        raise SkipTest("Need to be manually")
        try:
            self.conn.modules.sys.path[100000]
        except IndexError:
            print "type 'q' to exit"
            rpyc.utils.classic.post_mortem(self.conn)
            raise
        else:
            assert False, "expected an exception"
    
    def test_migration(self):
        l = rpyc.classic.obtain(self.conn.modules.sys.path)
        assert type(l) is list
        rl = rpyc.classic.deliver(self.conn, l)
        assert isinstance(rl, rpyc.BaseNetref)
