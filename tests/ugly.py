import os
import sys
import rpyc
import tempfile
import six
import subprocess
from rpyc.utils.splitbrain import splitbrain, localbrain
import traceback
import shutil
sys.excepthook = sys.__excepthook__


splitbrain.enable()
server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "rpyc_classic.py")
proc = subprocess.Popen([sys.executable, server_file, "--mode=oneshot", "--host=localhost", "-p0"], 
    stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
assert proc.stdout.readline().strip() == six.b("rpyc-oneshot")
host, port = proc.stdout.readline().strip().split(six.b("\t"))
conn = rpyc.classic.connect(host, int(port))

here = os.getcwd()
mypid = os.getpid()

with open("split-test.txt", "w") as f:
    f.write("foobar")

with splitbrain(conn):
    try:
#        path = tempfile.mkdtemp()
#        
#        import email
#        
#        assert "stale" not in repr(email)
#        
#        os.chdir(path)
#        hispid = os.getpid()
#        assert mypid != hispid
#        here2 = os.getcwd()
#        assert here != here2
#        assert not os.path.exists("split-test.txt")
#        with open("split-test.txt", "w") as f:
#            f.write("spam")
#        
#        with localbrain():
#            assert os.getpid() == mypid
#            with open("split-test.txt", "r") as f:
#                assert f.read() == "foobar"
#        
        try:
            open("crap.txt", "r")
        except (ValueError, OSError, IOError):
            pass
        else:
            assert False, "Expected IOError"
        
        print ("OK")
     
    finally:
        # we must move away from the tempdir to delete it (at least on windows)
        os.chdir("/")
        #shutil.rmtree(path)

#assert "stale" in repr(email)

assert os.getpid() == mypid
assert os.getcwd() == here

os.remove("split-test.txt")

conn.close()
splitbrain.disable()

