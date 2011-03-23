#!/usr/bin/env python
import sys
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2, 4):
    sys.exit("requires python 2.4 and up")

here = os.path.dirname(__file__)
exec("\n".join(open(os.path.join(here, 'rpyc', 'version.py')).read().splitlines()))

setup(name = "RPyC",
    version = version_string,
    description = "Remote Python Call (RPyC), a transparent and symmetric RPC library",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    license = "MIT",
    url = "http://rpyc.wikidot.com",
    download_url = "http://sourceforge.net/projects/rpyc/files/main/%s" % (version_string,),
    packages = [
        'rpyc', 
        'rpyc.core', 
        'rpyc.lib',
        'rpyc.utils', 
    ],
    scripts = [
        os.path.join("rpyc", "scripts", "rpyc_classic.py"),
        os.path.join("rpyc", "scripts", "rpyc_registry.py"),
        os.path.join("rpyc", "scripts", "rpyc_vdbconf.py"),
    ],
    platforms = ["POSIX", "Windows"],
    use_2to3 = True,
    zip_ok = False,
    #entry_points = {
    #    "console_scripts": [
    #         "rpyc_vdbconf = rpyc.scripts.vdbconf:main",
    #         "rpyc_classic = rpyc.scripts.rpyc_classic:main",
    #         "rpyc_registry = rpyc.scripts.rpyc_classic:main",
    #    ]
    #},
    long_description = ("A symmetric library for transparent RPC, clustering and "
        "distributed computing for python, built around the concept of remote "
        "services and object proxying"),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Object Brokering",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Clustering",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
)


