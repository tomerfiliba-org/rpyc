import socket
from subprocess import Popen, PIPE


# modified from the stdlib pipes module for windows
_safechars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@%_-+=:,./'
_funnychars = '"`$\\'
def shquote(text):
    if not text:
        return "''"
    for c in text:
        if c not in _safechars:
            break
    else:
        return text
    if "'" not in text:
        return "'" + text + "'"
    res = "".join(('\\' + c if c in _funnychars else c) for c in text)
    return '"' + res + '"'

class SshTunnel(object):
    PROGRAM = r"""import sys;sys.stdout.write("ready\n\n\n");sys.stdout.flush();sys.stdin.readline()"""
    
    def __init__(self, sshctx, loc_host, loc_port, rem_host, rem_port):
        self.loc_host = loc_host
        self.loc_port = loc_port
        self.rem_host = rem_host
        self.rem_port = rem_port
        self.sshctx = sshctx
        self.proc = sshctx.popen("python", "-u", "-c", self.PROGRAM, 
            L = "%s:%s:%s" % (loc_port, rem_host, rem_port))
        banner = self.proc.stdout.readline().strip()
        if banner != "ready":
            raise ValueError("tunnel failed")
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
    def __str__(self):
        return "%s:%s --> (%s)%s:%s" % (self.loc_host, self.loc_port, self.sshctx.host,
            self.rem_host, self.rem_port)
    def is_open(self):
        return self.proc and self.proc.poll() is None
    def close(self):
        if not self.is_open():
            return
        self.proc.stdin.write("foo\n\n\n")
        self.proc.stdin.close()
        self.proc.kill()
        self.proc.wait()
        self.proc = None

class SshContext(object):
    def __init__(self, host, user = None, port = None, keyfile = None, 
            ssh_program = "ssh", ssh_env = None, ssh_cwd = None,
            scp_program = "scp", scp_env = None, scp_cwd = None):
        self.host = host
        self.user = user
        self.port = port
        self.keyfile = keyfile
        self.ssh_program = ssh_program
        self.ssh_env = ssh_env
        self.ssh_cwd = ssh_cwd
        self.scp_program = scp_program
        self.scp_env = scp_env
        self.scp_cwd = scp_cwd

    def __str__(self):
        uri = "ssh://" + ("%s@%s" % (self.user, self.host) if self.user else self.host)
        if self.port:
            uri += ":%d" % (self.port)
        return uri
    
    def _convert_kwargs_to_args(self, kwargs):
        args = []
        for k, v in kwargs.iteritems():
            if v is True:
                args.append("-%s" % (k,))
            elif v is False:
                pass
            else:
                args.append("-%s" % (k,))
                args.append(str(v))
        return args

    def _process_scp_cmdline(self, kwargs):
        args = [self.scp_program]
        if self.keyfile and "i" not in kwargs:
            kwargs["i"] = self.keyfile
        if self.port and "P" not in kwargs:
            kwargs["P"] = self.port
        args.extend(self._convert_kwargs_to_args(kwargs))
        host = "%s@%s" % (self.user, self.host) if self.user else self.host
        return args, host
    
    def _process_ssh_cmdline(self, kwargs):
        args = [self.ssh_program]
        if self.keyfile and "i" not in kwargs:
            kwargs["i"] = self.keyfile
        if self.port and "p" not in kwargs:
            kwargs["p"] = self.port
        args.extend(self._convert_kwargs_to_args(kwargs))
        args.append("%s@%s" % (self.user, self.host) if self.user else self.host)
        return args
    
    def popen(self, *args, **kwargs):
        cmdline = self._process_ssh_cmdline(kwargs)
        cmdline.extend(shquote(a) for a in args)
        #print cmdline
        return Popen(cmdline, stdin = PIPE, stdout = PIPE, stderr = PIPE, 
            cwd = self.ssh_cwd, env = self.ssh_env, shell = False)

    def execute(self, *args, **kwargs):
        retcode = kwargs.pop("retcode", 0)
        proc = self.popen(*args, **kwargs)
        stdout, stderr = proc.communicate()
        if retcode is not None and proc.returncode != retcode:
            raise ValueError("process failed", stdout, stderr)
        return proc.returncode, stdout, stderr
    
    def upload(self, src, dst, **kwargs):
        cmdline, host = self._process_scp_cmdline(kwargs)
        cmdline.append(src)
        cmdline.append("%s:%s" % (host, dst))
        proc = Popen(cmdline, stdin = PIPE, stdout = PIPE, stderr = PIPE, 
            cwd = self.scp_cwd, env = self.scp_env)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise ValueError("upload failed", stdout, stderr)
    
    def download(self, src, dst, **kwargs):
        cmdline, host = self._process_scp_cmdline(kwargs)
        cmdline.append("%s:%s" % (host, src))
        cmdline.append(dst)
        proc = Popen(cmdline, stdin = PIPE, stdout = PIPE, stderr = PIPE, 
            cwd = self.scp_cwd, env = self.scp_env)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise ValueError("upload failed", stdout, stderr)
    
    def tunnel(self, loc_port, rem_port, loc_host = "localhost", rem_host = "localhost"):
        return SshTunnel(self, loc_host, loc_port, rem_host, rem_port)







