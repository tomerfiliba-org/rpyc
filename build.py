#!/usr/bin/env python
import os
import shutil
import subprocess
from optparse import OptionParser
from rpyc.version import version_string


def run(args, input = None, cwd = None, env = None, retcode = 0):
    proc = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE,
        stderr = subprocess.PIPE, cwd = None, env = None)
    out, err = proc.communicate(input)
    if proc.returncode != retcode:
        print( "===============================================================" )
        print( out )
        print( err )
        raise OSError("process failed")


def main(publish = False):
    shutil.rmtree("build", ignore_errors = True)
    shutil.rmtree("dist", ignore_errors = True)
    shutil.rmtree("MANIFEST", ignore_errors = True)
    
    # generate zip, tar.gz, win32 installer and egg
    run(["python", "setup.py", "sdist", "--formats=zip,gztar"])
    run(["python", "setup.py", "bdist_wininst", "--plat-name=win32"])
    run(["python", "setup.py", "bdist_egg"])
    # python 2.5 and 2.6 eggs
    run(["c:\\python25\\python.exe", "setup.py", "bdist_egg"])
    run(["c:\\python26\\python.exe", "setup.py", "bdist_egg"])
    
    if publish:
        # publish on pypi
        run(["python", "setup.py", "register"])
        
        # upload to sourceforge
        dst = "gangesmaster,rpyc@frs.sourceforge.net:/home/frs/project/r/rp/rpyc/main/%s/" % (version_string,)
        run(["scp"] + ["dist/%s" % (f,) for f in os.listdir("dist")] + [dst])

    shutil.rmtree("build", ignore_errors = True)
    shutil.rmtree("RPyC.egg-info", ignore_errors = True)



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--publish", action="store_true", dest="publish", default=False,
                      help="publish on pypi, sourceforge, tag in github")
    options, args = parser.parse_args()
    main(options.publish)


