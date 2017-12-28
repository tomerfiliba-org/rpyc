import rpyc
import gc

c = rpyc.classic.connect("localhost")
c.execute("""class Foo(object):
    def __init__(self, name):
        self.name = name
    def __del__(self):
        print "%s deleted" % (self.name,)
""")

f1 = c.namespace["Foo"]("f1")
f2 = c.namespace["Foo"]("f2")
f3 = c.namespace["Foo"]("f3")

del f1
del f2
gc.collect()

raw_input()
c.close()

