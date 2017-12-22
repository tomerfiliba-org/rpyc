import rpyc

conn = rpyc.connect("localhost", 12345)

remote_object = conn.root.remote_object


a = remote_object.remote_attr
remote_object.remote_attr
remote_object.remote_attr
remote_object.remote_attr
remote_object.remote_attr

oid = a.____oid__
#del a
#remote_object.____conn__()._remote_root.exposed_getconn()._local_objects._dict[oid][1]
print(conn.root.get()[oid][1])
