import rpyc

conn = rpyc.connect("localhost", 12345)

r = conn.root.use_list(['hello'])

print(r)
