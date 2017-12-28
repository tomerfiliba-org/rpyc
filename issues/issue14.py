import rpyc
import os
from contextlib import contextmanager

class Number(object):
    def __init__(self,number):
        self.number=number

def f(number):
    print( number.number)


@contextmanager
def ASYNC(func):
    wrapper = rpyc.async(func)
    yield wrapper

if __name__ == "__main__":
    conn = rpyc.classic.connect("localhost")
    conn.modules.sys.path.append(os.path.dirname(__file__))

    mod = conn.modules["issue14"]
    n = Number(999)
    #f = rpyc.async(mod.f)(n)
    #print( f )
    #print( f.value )

    f2 = rpyc.async(mod.f)
    res = f2(n)
    print res.value
    
    with ASYNC(mod.f) as f2:
        res = f2(n)
        print res.value


