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


class HelloService(rpyc.Service):
    def exposed_concat(self, remote_str):
        local_str = ' github'
        return remote_str + local_str


if __name__ == "__main__":
    rpyc.lib.setup_logger()
    server = OneShotServer(HelloService, port=12345)
    server.start()
```

Client:

```python
import rpyc


if __name__ == "__main__":
    c = rpyc.connect("localhost", 12345)
    print(c.root.concat('hello'))
```
