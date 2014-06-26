#!/usr/bin/env python
from __future__ import print_function
from plumbum import local, cli
from plumbum.path.utils import delete
from rpyc.version import version_string

class Build(cli.Application):
    publish = cli.Flag("--publish")
    
    def main(self):
        delete("build", "dist", "MANIFEST", local.cwd // "*.egg-info")

        # generate zip, tar.gz, and win32 installer
        if self.publish:
            print("registering...")
            local.python("setup.py", "register")
            print("uploading zip and tar.gz")
            local.python("setup.py", "sdist", "--formats=zip,gztar", "upload")
            print("uploading win installer")
            local.python("setup.py", "bdist_wininst", "--plat-name=win32", "upload")
        else:
            local.python("setup.py", "sdist", "--formats=zip,gztar")
            local.python("setup.py", "bdist_wininst", "--plat-name=win32")
    
        delete("build", local.cwd // "*.egg-info")
        print("Built", [f.basename for f in local.cwd / "dist"])

if __name__ == "__main__":
    Build.run()

