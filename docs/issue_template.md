Describe the issue briefly here, including:

- expected result versus actual result
- involved/problematic methods, e.g. `__call__`
- steps to reproduce
- for bugs, please attach a

```
stack trace / error log
```


##### Environment

- rpyc version
- python version
- operating system


##### Minimal example

Server:

```python
import rpyc
from rpyc.utils.server import OneShotServer
rpyc.lib.setup_logger()

class ListService(rpyc.Service):
    def exposed_concat(self, lst):
        return lst + ['world']

server = OneShotServer(ListService, port=12345)
server.start()
```

Client:

```python
import rpyc
c = rpyc.connect("localhost", 12345)
print(c.root.concat(['hello']))
```
