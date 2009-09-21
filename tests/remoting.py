from testbase import TestBase
import rpyc


class Remoting(TestBase):
    def setup(self):
        self.cannot_run("not implemented yet")
        self.conn = rpyc.classic.connect_thread()
    def cleanup(self):
        self.conn.close()
    
    def step_files(self):
        pass
    
    def step_interactive(self):
        pass

    
    
if __name__ == "__main__":
    Remoting.run()

