import rpyc

#
# with explicit closing
#
for i in range(5000):
    #if i % 100 == 0:
    #    print i
    c = rpyc.ssl_connect("localhost", 13388, keyfile = "cert.key", certfile = "cert.crt")
    print i, c.fileno()
    #c = rpyc.connect("localhost", 13388)
    assert c.root.foo() == 18
    c.close()

print
print "finished (1/2)"

#
# without explicit closing
#
for i in range(5000):
    if i % 100 == 0:
        print i
    c = rpyc.ssl_connect("localhost", 13388, keyfile = "cert.key", certfile = "cert.crt")
    #c = rpyc.connect("localhost", 13388)
    assert c.root.foo() == 18
    #c.close()

print
print "finished (2/2)"

