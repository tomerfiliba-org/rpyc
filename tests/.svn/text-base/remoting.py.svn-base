from testbase import TestBase
import rpyc
import os
import tempfile
import shutil


class Remoting(TestBase):
    def setup(self):
        self.conn = rpyc.classic.connect_thread()
    
    def cleanup(self):
        self.conn.close()
    
    def step_files(self):
        base = tempfile.mkdtemp()
        base1 = os.path.join(base, "1")
        base2 = os.path.join(base, "2")
        base3 = os.path.join(base, "3")
        os.mkdir(base1)
        for i in range(10):
            open(os.path.join(base1, "foofoo%d" % (i,)), "w")
        os.mkdir(os.path.join(base1, "somedir1"))
        
        rpyc.classic.upload(self.conn, base1, base2)
        self.require(os.listdir(base1) == os.listdir(base2))
        
        rpyc.classic.download(self.conn, base2, base3)
        self.require(os.listdir(base2) == os.listdir(base3))
        
        shutil.rmtree(base)
    
    def step_distribution(self):
        self.log("TODO: upload package")
        self.log("TODO: update module")
    
    def step_interactive(self):
        self.log("type Ctrl+D to exit (Ctrl+Z on Windows)")
        rpyc.classic.interact(self.conn)
    
    def step_post_mortem(self):
        try:
            self.conn.modules.sys.path[100000]
        except IndexError:
            self.log("type 'q' to exit")
            rpyc.classic.pm(self.conn)
        else:
            self.fail("expected an exception")
    
    def step_migration(self):
        l = rpyc.classic.obtain(self.conn.modules.sys.path)
        self.require(type(l) is list)
        rl = rpyc.classic.deliver(self.conn, l)
        self.require(isinstance(rl, rpyc.BaseNetref))


if __name__ == "__main__":
    Remoting.run()

