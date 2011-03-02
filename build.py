#!/usr/bin/env python
import time
import subprocess
from optparse import OptionParser

def run(args, input = None, cwd = None, env = None, retcode = 0):
    proc = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE,
        stderr = subprocess.PIPE, cwd = None, env = None)
    out, err = proc.communicate(input)
    if proc.returncode != retcode:
        raise OSError("process failed")


def main(publish = False):
    # generate zip, tar.gz, win32 installer and egg
    run(["python", "setup.py", "sdist", "--formats=zip,gztar"])
    run(["python", "setup.py", "bdist_wininst", "--plat-name=win32"])
    run(["python", "setup.py", "bdist_egg"])
    
    if publish:
        # tag in git
        msg = "release %s (%s)" % (rpyc.version_string, time.asctime())
        run(["git", "tag", "-a", "-f", "-m", msg, rpyc.version_string])
        run(["git", "push", "--tag"])

        # publish on pypi
        run(["python", "setup.py", "register"])
        
        # upload to sourceforge
        dst = "gangesmaster,rpyc@frs.sourceforge.net:/home/frs/project/r/rp/rpyc/%s/" % (rpyc.version_string,)
        run(["scp", "-r", "dist", dst])




if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--public", action="store_true", dest="public", default=False,
                      help="public on pypi, sourceforge, tag in github")
    options, args = parser.parse_args()
    main(options.publish)


