import rpyc
import time
import os


filename = "/tmp/floop.bloop"
if os.path.exists(filename):
    os.remove(filename)

f = open(filename, "w")
conn = rpyc.connect("localhost", 18871)
bgsrv = rpyc.BgServingThread(conn)  # create a bg thread to process incoming events

def on_file_changed(oldstat, newstat):
    print( "file changed")
    print( "    old stat: %s" % (oldstat,))
    print( "    new stat: %s" % (newstat,))

mon = conn.root.FileMonitor(filename, on_file_changed) # create a filemon

print( "wait a little for the filemon to have a look at the original file")
time.sleep(2)

print( "change file size")
f.write("shmoop") # change size
f.flush()
time.sleep(2)

print( "change size again")
f.write("groop") # change size
f.flush()
time.sleep(2)

mon.stop()
bgsrv.stop()
conn.close()

