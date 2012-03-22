rpycfs -- a remote file system (like sambda of nfs)

it should be quite easy, subclassing Fuse and exposing a file-system like
interface above it, and then use rpyc to perform the IOs, but i find
python-fuse to be quite confusing and i lost interest in the project.
sorry.
if someone wants to contribute the code, i'll happily include it in the demos.

it should look something like this:
    # server
    rpycfsd /path/to/expose --port=12345 --user=foo --password=bar

    # client
    /sbin/mount.rpycfs host:/relativepath /localpoint -o port=12345 -o user=foo -o password=bar

