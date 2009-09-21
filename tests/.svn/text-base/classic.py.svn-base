from testbase import TestBase
import rpyc


class Classic(TestBase):
    def setup(self):
        self.conn = rpyc.classic.connect_thread()
    def cleanup(self):
        self.conn.close()
    
    def step_piped_server(self):
        conn2 = rpyc.classic.connect_subproc()
        conn2.modules.sys.path.append("xxx")
        self.require(conn2.modules.sys.path.pop(-1), "xxx")
        conn2.close()
        self.require(conn2.proc.wait() == 0)
    
    def step_buffiter(self):
        bi = rpyc.buffiter(self.conn.modules.__builtin__.xrange(10000))
        self.require(list(bi) == range(10000))
    
    def step_classic(self):
        self.log(self.conn.modules.sys)
        self.log(self.conn.modules["xml.dom.minidom"].parseString("<a/>"))
        self.conn.execute("x = 5")
        self.require(self.conn.namespace["x"] == 5)
        self.require(self.conn.eval("1+x") == 6)
    
    def step_isinstance(self):
        x = self.conn.modules.__builtin__.range(10)
        self.log(x)
        self.log(type(x))
        self.log(x.__class__)
        self.require(isinstance(x, list))


if __name__ == "__main__":
    Classic.run()

