# Testing Supported Python Versions via Docker
In order to test RPyC locally, across different Python versions, the preferred method is to use Docker. Every version of Python RPyC supports is configured; you should run `cd docker` and then start the containers by running `docker-compose up`. The schema used for container names is `rpyc-3.<minor-version>`.

For example, running these two commands in separate terminals will write `hello world` to the server-side console.
```
docker exec -it rpyc-3.7 /opt/rpyc/bin/rpyc_classic.py --host 0.0.0.0
docker exec -it rpyc-3.10 python -c "import rpyc;conn = rpyc.utils.classic.connect('rpyc-3.7'); conn.modules.sys.stderr.write('hello world\n')"
```
