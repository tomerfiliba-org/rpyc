from __future__ import with_statement
from contextlib import contextmanager
import rpyc


class BatchingService(object):
    def exposed_execute(self, code):
        pass

OPCODE_NOP = "noop"
OPCODE_GETATTR = "gatr"
OPCODE_DELATTR = "datr"
OPCODE_CALL = "call"

class InstructionBatch(object):
    def __init__(self, conn):
        self.conn = conn
        self.opcodes = []
        self.values = []
        self.locals = []
    
    def add(self, opcode, args):
        self.opcodes.append((opcode, ))
    
    def commit(self):
        for oc in self.opcodes:
            print oc
        #self.conn.root.batching.execute()

class Batching(object):
    def __init__(self, instbatch, opcode, *args):
        self.__instbatch = instbatch
        self.__instbatch.add(opcode, args)
    def __getattr__(self, name):
        return Batching(self.__instbatch, OPCODE_GETATTR, self, name)
    def __call__(self, *_a, **_k):
        return Batching(self.__instbatch, OPCODE_CALL, _a, _k)

@contextmanager
def batched(proxy):
    ib = InstructionBatch(proxy.____conn__)
    yield Batching(ib, OPCODE_NOP, proxy)
    ib.commit()


if __name__ == "__main__":
    import rpyc
    
    class MyService(rpyc.Service):
        batching = BatchingService()
        
        def exposed_range(self, n):
            return range(n)
    
    conn = rpyc.connect_thread(MyService, remote_service = MyService)
    rl = conn.root.range(10)
    with batched(rl) as bl:
        bl.append("foo")
        bl.append("bar")
    print rl



































