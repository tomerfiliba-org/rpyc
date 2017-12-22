import rpyc
import traceback
import time

# make sure we open enough fd and keep them to go beyond 1024
c = []
for i in range(1030):
    try:
        c.append(open('/dev/null'))
    except OSError:
        print(i)
        raise

# establish an RPyC connection
rpcconn = rpyc.connect('localhost', 18812)
remote_root_ref = rpcconn.async_request(rpyc.core.consts.HANDLE_GETROOT)
remote_root_ref.set_expiry(1.0)
c.append(rpcconn)
try:
  # use it - this calls Stream.poll(), which actually is a select() ...
  rpcconn._remote_root = remote_root_ref.value
  print('Successfully connected, waiting 10 secs before terminating...')
  time.sleep(10)
except Exception as e:
  print(i, e)
  traceback.print_exc()
