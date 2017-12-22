import rpyc
import time

try:
    connection = rpyc.connect("localhost", 18861,
                    config={'allow_all_attrs':True,
                            'allow_pickle':True})
    bgt = rpyc.BgServingThread(connection)

    start = time.time()
    data = connection.root.fetch_stuff()

    [str(x.intvalue) for x in data]
    ['%s-'%x.stringvalue for x in data]

    end = time.time()
    print(end - start)

    #connection.root.put_stuff(data)
except Exception, e:
    print e
