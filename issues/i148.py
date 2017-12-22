import rpyc
c = rpyc.classic.connect("127.0.0.1")
f = c.modules.os.popen("ping www.google.com -c 3")
for l in f:
    print(l)

# import os
# f = os.popen("ping www.google.com -c 5")
# for l in f:
#     print(l)
