v3.3
====
Scheduled for August/September 2012

* Will integrate with `plumbum`:

  * SSHContext/ SSHTunnel will be killed in favor of plumbum tunnelling
  * CLI argument processing (``rpyc_classic.py``, etc) will be replaced by plumbum.cli

* Daemon (rpycd) - use the ``daemon`` module to provide a UNIX rpyc_classic daemon (to be used in init scripts, etc.)

* Zerodeploy - using plumbum, you would be able to connect to a remote machine, copy RPyC to a temporary directory,
  run it over there and create an SSH tunnel to it, in a single line of code. This would mean enable you to 
  deploy RPyC on remote machines easily, and start/stop the server externally.
