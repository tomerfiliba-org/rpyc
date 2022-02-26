.. _advdebugging:

Advanced Debugging
==================

A guide to using Wireshark when debugging complex use such as chained-connections or version specific issues. To test more complex issues, we may wish to use `pyenv` or Docker in our development environment.

Testing Supported Python Versions via pyenv
--------------------------------------------
Let's use `pyenv` to install Python versions under active development. Since development versions are pulled from a VCS, we wish to force install to get the latest commit before testing. The dependency `plumbum` needs to be installed as well (add `[dev]` for `plumbum` development dependencies). All together now!

.. code-block:: bash

    versions=( 3.7-dev 3.8-dev 3.9-dev 3.10-dev 3.11-dev )
    for ver in ${versions[@]}; do
        pyenv install --force ${ver}
        pyenv global ${ver}
        pyenv exec pip install --upgrade pip setuptools wheel plumbum[dev]
        site="$(pyenv exec python -c 'import site; print(site.getsitepackages()[0])')"
        printf "${PWD}\n" > "${site}/rpyc.pth"
    done

Each `venv` contains a `.pth` file that appends `rpyc` to `sys.path`.

.. code-block:: bash

    PYENV_VERSION=3.11-dev pyenv exec python ./bin/rpyc_classic.py --host 127.0.0.1
    PYENV_VERSION=3.10-dev pyenv exec python -c "import rpyc; conn = rpyc.utils.classic.connect('127.0.0.1'); conn.modules.sys.stderr.write('hello world\n')"


Testing Supported Python Versions via Docker
--------------------------------------------
Testing RPyC often requires that you use specific Python versions. Docker will make your life easier when testing RPyC locally, especially when performing packet captures of RPyC communication across Python versions. The current settings will use bind mounts to simplify synchronization of RPyC source code within the containers. So, remember to checkout the commit you desire the containers to use on your host!

If desired, individual containers can be specified started

.. code-block:: bash

    docker-compose -f ./docker/docker-compose.yml create
    docker-compose -f ./docker/docker-compose.yml start rpyc-python-3.7
    docker-compose -f ./docker/docker-compose.yml start rpyc-python-3.10

The registry server can be started like so

.. code-block:: bash

    docker exec rpyc-3.8 /opt/rpyc/bin/rpyc_registry.py

The containers can then be used to test to your hearts desire

.. code-block:: bash

    docker exec rpyc-3.7 /opt/rpyc/bin/rpyc_classic.py --host 0.0.0.0 &
    docker exec -it rpyc-3.10 python -c "import rpyc;conn = rpyc.utils.classic.connect('rpyc-3.7'); conn.modules.sys.stderr.write('hello world\n')"


Tips and Tricks
---------------
Display filtering for Wireshark

.. code-block:: output

    tcp.port == 18878 || tcp.port == 18879
    (tcp.port == 18878 || tcp.port == 18879) && tcp.segment_data contains "rpyc.core.service.SlaveService"

Running the chained-connection unit test

.. code-block:: bash

    cd tests
    python  -m unittest test_get_id_pack.Test_get_id_pack.test_chained_connect


After stopping Wireshark, export specified packets, and open the PCAP. If not already configured, add a custom display column:

.. code-block:: output

    Title,        Type,   Fields,     Field Occurrence
    Stream Index, Custom, tcp.stream, 0

The stream index column makes it easier to decide which TCP stream to follow. Following a TCP provides a more human readable overview
of requests and replies that can be printed as a PDF.

.. figure:: _static/advanced-debugging-chained-connection-w-wireshark.png
