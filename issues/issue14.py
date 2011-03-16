import rpyc 
import os

class Number(object): 
    def __init__(self,number): 
        self.number=number 

def f(number): 
    print( number.number) 


if __name__ == "__main__": 
    conn = rpyc.classic.connect("localhost")
    conn.modules.sys.path.append(os.path.dirname(__file__)) 
    
    mod = conn.modules["issue14"] 
    n = Number(999) 
    f = rpyc.async(mod.f)(n)
    print( f )
    print( f.value )
    
    #proxy = rpyc.async(mod.f) 
    #f = proxy(n) 
    #f.value
