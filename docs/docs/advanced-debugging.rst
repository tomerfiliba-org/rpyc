.. _advdebugging:

Advanced Debugging
==================

A guide to using Wireshark when debugging complex use such as chained-connections.

Testing Supported Python Versions via Docker
--------------------------------------------
Testing RPyC often requires that you use specific Python versions. Docker will make your life easier when testing RPyC locally, especially when performing packet captures of RPyC communication across Python versions. The current settings will use bind mounts to simplify synchronization of RPyC source code within the containers. So, remember to checkout the commit you desire the containers to use on your host!

If desired, individual containers can be specified started ::

    docker-compose -f ./docker/docker-compose.yml create
    docker-compose -f ./docker/docker-compose.yml start rpyc-python-3.7
    docker-compose -f ./docker/docker-compose.yml start rpyc-python-3.10

The registry server can be started like so ::

    docker exec rpyc-3.8 /opt/rpyc/bin/rpyc_registry.py

The containers can then be used to test to your hearts desire ::

    docker exec rpyc-3.7 /opt/rpyc/bin/rpyc_classic.py --host 0.0.0.0 &
    docker exec -it rpyc-3.10 python -c "import rpyc;conn = rpyc.utils.classic.connect('rpyc-3.7'); conn.modules.sys.stderr.write('hello world\n')"


Tips and Tricks
---------------
Display filtering for Wireshark ::

    tcp.port == 18878 || tcp.port == 18879
    (tcp.port == 18878 || tcp.port == 18879) && tcp.segment_data contains "rpyc.core.service.SlaveService"

Running the chained-connection unit test ::

    cd tests
    python  -m unittest test_get_id_pack.Test_get_id_pack.test_chained_connect


After stopping Wireshark, export specified packets, and open the PCAP. If not already configured, add a custom display column: ::

    Title,        Type,   Fields,     Field Occurrence
    Stream Index, Custom, tcp.stream, 0

The stream index column makes it easier to decide which TCP stream to follow. Following a TCP provides a more human readable overview
of requests and replies that can be printed as a PDF.

.. figure:: _static/advanced-debugging-chained-connection-w-wireshark.png
