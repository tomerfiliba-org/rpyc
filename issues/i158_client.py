import rpyc

class MyStruct(object):
    pass

conn = rpyc.connect("localhost", 12345)

conn.ping(MyStruct())

remote_fun = rpyc.async(conn.root.fun)

res1 = remote_fun("aa", MyStruct())
res2 = remote_fun("bb", MyStruct())

print(res1.value, res2.value)

input()
