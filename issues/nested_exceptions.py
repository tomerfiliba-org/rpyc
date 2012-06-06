import rpyc
c=rpyc.classic.connect_thread()
c.execute("import rpyc; c2=rpyc.classic.connect_thread()")
c.namespace["c2"].execute("1/0")

