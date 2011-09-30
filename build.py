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

    # generate zip, tar.gz, and win32 installer
    if publish:
        print("registering...")
        run(["python", "setup.py", "register"])
        print("uploading zip and tar.gz")
        run(["python", "setup.py", "sdist", "--formats=zip,gztar", "upload"])
        print("uploading win installer")
        run(["python", "setup.py", "bdist_wininst", "--plat-name=win32", "upload"])

        # upload to sourceforge
        print("uploading to sourceforge")
        dst = "gangesmaster,rpyc@frs.sourceforge.net:/home/frs/project/r/rp/rpyc/main/%s/" % (version_string,)
        run(["rsync", "-rv", "dist/", dst])
    else:
        run(["python", "setup.py", "sdist", "--formats=zip,gztar"])
        run(["python", "setup.py", "bdist_wininst", "--plat-name=win32"])

    shutil.rmtree("build", ignore_errors = True)
    shutil.rmtree("RPyC.egg-info", ignore_errors = True)
    shutil.rmtree("rpyc.egg-info", ignore_errors = True)



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--publish", action="store_true", dest="publish", default=False,
                      help="publish on pypi, sourceforge, tag in github")
    options, args = parser.parse_args()
    main(options.publish)

