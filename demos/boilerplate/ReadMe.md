# Generic RPyC service boiler plate

This service is ispired by the FileMonitor example.

It will monitor the file `/tmp/test.txt` to geenrate asynchrounous events that will be notified to the RPyC client.

run in one terminal:

    python3 rpyc_server.py
    
run is a second terminal:

    python3 rpyc_client.py

at the server console:

    news client with /tmp/test.txt <bound method MyClient.on_event of <__main__.MyClient object at 0x7f40bd1e3070>>

then open a third terminal and give some commands like:

    touch /tmp/test.txt
    
you should read from the client console:

    file changed
        old stat: os.stat_result(st_mode=33204, st_ino=1181245, st_dev=2053, st_nlink=1, st_uid=1000, st_gid=1000, st_size=0, st_atime=1596994889, st_mtime=1596994889, st_ctime=1596994889)
        new stat: os.stat_result(st_mode=33204, st_ino=1181245, st_dev=2053, st_nlink=1, st_uid=1000, st_gid=1000, st_size=0, st_atime=1596995295, st_mtime=1596995295, st_ctime=1596995295)

then after 30s at the server console you see:

        client closed.
