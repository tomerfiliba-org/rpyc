import fcntl
import os
import socket
import select
import string
import subprocess
import sys
import time

import protocol

from cStringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED

__all__ = [ 'SshConnection' ]

_mod_trans = string.maketrans('.', '/')
_py_roots = [ ]
_py_data = [ None ]
_py_python = [ None ]

def sortuniq(alist):
    retset = {}
    map(retset.__setitem__, alist, [])
    retset = retset.keys()
    retset.sort()
    return retset

def set_py_modules(modules=None):
    if modules is None:
        modules = []
    import rpyc
    if rpyc not in modules:
        modules.append(rpyc)
    roots = []
    for mod in modules:
        if hasattr(mod, '__file__'):
            roots.append(os.path.abspath(os.path.dirname(mod.__file__)) + '/')
    roots = sortuniq(roots)
    if roots != _py_roots:
        _py_roots[:] = roots
        _py_data[0] = None

def set_python(python=None):
    _py_python[0] = python

def get_python(python=None):
    return _py_python[0]

def get_py_data():
    set_py_modules()
    if _py_data[0] is not None:
        return _py_data[0]
    modules = []
    for modname, mod in sys.modules.items():
        if hasattr(mod, '__file__'):
            modfile = os.path.abspath(mod.__file__)
            for root in _py_roots:
                if modfile.startswith(root):
                    if modfile.endswith('.pyc') or modfile.endswith('.pyo'):
                        modfile = modfile[:-1]
                    if not modfile.endswith('.py'):
                        raise ValueError, 'Unsupported module file:' + modfile
                    modules.append((modname, modfile))
                    break
    zdata = StringIO()
    zfile = ZipFile(zdata, 'w', ZIP_DEFLATED)
    modules.sort(key=lambda x: x[0])
    for modname, modfile in modules:
        if modfile.endswith('__init__.py'):
            modname = modname.translate(_mod_trans) + '/__init__.py'
        else:
            modname = modname.translate(_mod_trans) + '.py'
        zfile.write(modfile, modname)
    zfile.close()
    zdata.seek(0)
    _py_data[0] = zdata.read()
    return _py_data[0]

class FdIo(object):
    WRITE_SIZE = READ_SIZE = 4096

    def __init__(self, fd):
        self._fd = fd
        fcntl.fcntl(self._fd, fcntl.F_SETFL, os.O_NDELAY)
        self._buffer = ''
        self._eof = False

    def __del__(self):
        if hasattr(self, '_fd'):
            os.close(self._fd)
            del self._fd

    def fileno(self):
        return self._fd

    def read(self, count, timeout=None):
        if self._eof:
            raise ValueError, "EOF"
        if len(self._buffer) >= count:
            retval = self._buffer[:count]
            self._buffer = self._buffer[count:]
            return retval
        p = select.poll()
        p.register(self._fd, select.POLLIN)
        if timeout is None:
            end_time = None
        else:
            end_time = time.time() + timeout
        while True:
            if end_time:
                poll_timeout = max(0, int((end_time - time.time()) * 1000))
            else:
                poll_timeout = None
            if p.poll(poll_timeout):
                chunk = os.read(self._fd, self.READ_SIZE)
                if len(chunk) == 0:
                    retval = self._buffer
                    self._buffer = ''
                    self._eof = True
                    break
                self._buffer += chunk
                if len(self._buffer) >= count:
                    retval = self._buffer[:count]
                    self._buffer = self._buffer[count:]
                    break
            elif timeout is not None:
                retval = self._buffer
                self._buffer = ''
                break
        return retval

    def write(self, buf, timeout=None):
        count = os.write(self._fd, buf)
        if count >= len(buf):
            return count
        p = select.poll()
        p.register(self._fd, select.POLLOUT)
        if timeout is None:
            end_time = None
        else:
            end_time = time.time() + timeout
        while True:
            if end_time:
                poll_timeout = max(0, int((end_time - time.time()) * 1000))
            else:
                poll_timeout = None
            if p.poll(poll_timeout):
                count += os.write(self._fd, buf[count:])
                if count >= len(buf):
                    break
            elif timeout is not None:
                break
        return count

def make_initcode(datalen, binary=None):
    '''Return init code for starting RPyc on Python 2.4 or higher on the
       remote host after ssh has been started running sh.  The datalen arg
       is size of the zipfile of python source code to prepend to PYTHONPATH
       on the remote.
       '''
    if not binary:
        binary = 'python'
    return (
        "a=$(mktemp /tmp/tmpXXXXXX);exec 3>$a 2>/dev/null;" +
        "cat 1>&3 <<'0EOF'\n" +
        "import os, sys\n" +
        "if sys.version_info[0] != 2 or sys.version_info[1] < 4:\n" +
        "    try: os.execvp('python2.4', ['python2.4'] + sys.argv)\n" +
        "    except: pass\n" +
        "    try: os.execvp('python2.5', ['python2.5'] + sys.argv)\n" +
        "    except: pass\n" +
        "    try: os.execvp('python2.6', ['python2.6'] + sys.argv)\n" +
        "    except: pass\n" +
        "    sys.exit(1)\n" +
        "import select, tempfile\n" +
        "fd, fname = tempfile.mkstemp()\n" +
        "zbuf = ''\n" +
        "zbufsize = int(sys.argv[1])\n" +
        "os.write(sys.stdout.fileno(), 'SYNC1\\n')\n" +
        "while len(zbuf) < zbufsize:\n" +
        "    buf = os.read(sys.stdin.fileno(), zbufsize - len(zbuf))\n" +
        "    if not buf:\n" +
        "        sys.exit(1)\n" +
        "    zbuf += buf\n" +
        "os.write(fd, zbuf)\n" +
        "sys.path.insert(0, fname)\n" +
        "import rpyc\n" +
        "origstdin, origstdout = sys.stdin, sys.stdout\n" +
        "os.close(fd)\n" +
        "os.unlink(fname)\n" +
        "os.unlink(sys.argv[2])\n" +
        "os.write(origstdout.fileno(), 'SYNC2\\n')\n" +
        "rpyc.classic.connect_pipes(origstdin, origstdout).serve_all()\n" +
        "0EOF\nexec 3<&3;TMP=/tmp TEMP=/tmp exec %s -u $(readlink /proc/self/fd/3) %d $a\n" % (binary, datalen)
    )

def do_sync(expected, fileobj):
    syncbuf = ''
    while syncbuf.find(expected[:-1]) == -1:
        rlist, wlist, xlist = \
            select.select([fileobj], [], [], 5.0)
        if not rlist:
            raise IOError, 'session startup failed (timeout) ' \
                           + expected
        syncbuf = syncbuf[-(len(expected)-1):]
        buf = os.read(fileobj.fileno(), len(expected) - len(syncbuf))
        if not buf:
            raise IOError, 'session startup failed (i/o) ' \
                           + expected
        syncbuf += buf

class SubprocConnection(protocol.Connection):

    def _set_controlling_tty(self, ttyname):
        fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
        if fd >= 0:
            os.close(fd)
        os.setsid()
        try:
            fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
            if fd >= 0:
                os.close(fd)
                raise OSError, 'unable to disconnect from controlling tty'
        except:
            pass

        fd = os.open(ttyname, os.O_RDWR)
        if fd < 0:
            raise OSError, 'unable to open provided terminal device'
        else:
            os.close(fd)

        fd = os.open('/dev/tty', os.O_RDWR)
        if fd < 0:
            raise OSError, 'unable to open new controlling tty'
        else:
            os.close(fd)

    def __del__(self):
        if hasattr(self, '_proc') and hasattr(self._proc, 'returncode'):
            if self._proc.returncode is None:
                try: os.kill(self._proc.pid, 9)
                except OSError: pass
            del self._proc

    def _set_proc(self, cmd):
        '''Set the command, should produce 'SYNC0\n' when ready'''
        mfd, sfd = os.openpty()
        self._pty = FdIo(mfd)
        self._pty_slave = FdIo(sfd)
        slavetty = os.ttyname(sfd)
        self._proc = subprocess.Popen(cmd,
                preexec_fn=lambda:self._set_controlling_tty(slavetty),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

    def __init__(self):
        # Wait for initial control shell to be ready
        do_sync('SYNC0\n', self._proc.stdout)

        py_data = get_py_data()
        python = get_python()

        # Start up python
        os.write(self._proc.stdin.fileno(),
                 make_initcode(len(py_data), python))

        # Wait for python to completely start up
        do_sync('SYNC1\n', self._proc.stdout)

        # Feed remote python libraries
        os.write(self._proc.stdin.fileno(), py_data)

        # Wait for remote to be ready for RPC link init
        do_sync('SYNC2\n', self._proc.stdout)

        # Start up RPC link
        rpyc.Connection.__init__(self, rpyc.SlaveService,
            rpyc.Channel(rpyc.PipeStream(self._proc.stdout, self._proc.stdin)),
            {})

class SshConnection(SubprocConnection):

    def __init__(self, hostname, username=None, password=None, port=None,
                 identity=None, modules=None, python=None, options=None):
        if modules is not None:
            set_py_modules(modules)
        set_python(python)

        cmd = [ 'ssh', '-o', 'StrictHostKeyChecking no',
                       '-o', 'UserKnownHostsFile /dev/null',
                       '-e', 'none',
                       '-A']
        if username is not None:
            cmd.extend(['-l', username])
        if port is not None:
            cmd.extend(['-p', str(port)])
        if identity is not None:
            cmd.extend(['-i', identity])
        if options is not None:
            for option, value in options.items():
                cmd.extend(['-o', option + "=" + value])

        cmd.extend([hostname, 'sh', '-c', '"echo SYNC0;exec sh"'])

        self._set_proc(cmd)

        try:
            p = select.poll()
            p.register(self._pty.fileno(), select.POLLIN)
            p.register(self._proc.stdout.fileno(), select.POLLIN)
            p.register(self._proc.stderr.fileno(), select.POLLIN)

            errbuf = ''
            prompt = ''
            startup_complete = False
            while not startup_complete:
                plist = p.poll(5000)
                if not plist:
                    raise IOError, 'ssh session timed out'
                for pfd, pevent in plist:
                    if pfd == self._pty.fileno():
                        # password prompt
                        prompt += self._pty.read(1024, timeout=0.05)
                        if prompt.strip(' \t\r\n').endswith('assword:') or \
                           prompt.strip(' \t\r\n').endswith('esponse:'):
                            prompt = ''
                            if password is not None:
                                self._pty.write(password + '\r\n')
                            else:
                                raise IOError, 'ssh session required password'
                    if pfd == self._proc.stderr.fileno():
                        buf = os.read(self._proc.stderr.fileno(), 4096)
                        if not buf:
                            raise IOError, 'ssh session setup failed'
                        errbuf += buf
                    if pfd == self._proc.stdout.fileno():
                        startup_complete = True
        except IOError, e:
            e.stderr = errbuf
            raise e
        SubprocConnection.__init__(self)

