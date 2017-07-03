.. _classic:

Classic
=======
Prior to version 3, RPyC employed a modus-operandi that's now referred to as
"classic mode". In this mode, the server was completely under the control of its
client -- there was no way to restrict what the client could do, and there was
no notion of :ref:`services <services>`. A client simply connected to a server
and began to manipulate it.

Starting with version 3, RPyC became *service-oriented*, and now servers expose
well-defined *services*, which define what a client can access. However, since the
classic mode proved very useful and powerful, especially in testing environments,
and in order to retain backwards compatibility, the classic mode is still exists
in current versions -- this time implemented as a :class:`service <rpyc.core.service.SlaveService>`.

See also the :ref:`API reference <api-classic>`

Usage
-----
RPyC installs ``rpyc_classic.py`` to your Python scripts directory (e.g., ``C:\PythonXX\Scripts``,
``/usr/local/bin``, etc.), which is a ready-to-run classic-mode server. It can be configured
with :ref:`command-line parameters <classic-server>`. Once you have it running, you can connect
to it like so ::

    conn = rpyc.classic.connect("hostname")    # use default TCP port (18812)

    proc = conn.modules.subprocess.Popen("ls", stdout = -1, stderr = -1)
    stdout, stderr = proc.communicate()
    print stdout.split()

    remote_list = conn.builtin.range(7)

    conn.execute("print 'foo'")


